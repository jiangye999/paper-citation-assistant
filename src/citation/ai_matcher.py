"""
基于AI的语义匹配模块
使用大语言模型理解句子含义和论文摘要，进行智能匹配
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import requests

from ..literature.db_manager import LiteratureDatabaseManager, Paper
from ..draft.analyzer import Sentence


@dataclass
class AIMatchResult:
    """AI匹配结果"""

    paper: Paper
    relevance_score: float  # 0.0-1.0，AI语义评分
    relevance_reason: str  # 匹配理由说明
    confidence: str  # 置信度: high, medium, low
    composite_score: float = 0.0  # 综合分数（语义+新颖度+引用）


@dataclass
class SentenceWithAICitations:
    """带AI引用的句子"""

    sentence: Sentence
    citations: List[AIMatchResult] = field(default_factory=list)


class AIAPIManager:
    """API管理器 - 支持多种AI模型"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepseek.com/v1",
        model: str = "deepseek-chat",
        provider: str = "deepseek",
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.provider = provider.lower()

    def call_model(
        self, messages: List[Dict], temperature: float = 0.3, max_tokens: int = 2000
    ) -> str:
        """调用AI模型"""
        if self.provider == "deepseek":
            return self._call_deepseek(messages, temperature, max_tokens)
        elif self.provider == "openai":
            return self._call_openai(messages, temperature, max_tokens)
        elif self.provider == "anthropic":
            return self._call_anthropic(messages, temperature, max_tokens)
        else:
            raise ValueError(f"不支持的API提供商: {self.provider}")

    def _call_deepseek(
        self, messages: List[Dict], temperature: float, max_tokens: int
    ) -> str:
        """调用DeepSeek API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        response = requests.post(
            f"{self.base_url}/chat/completions", headers=headers, json=data, timeout=60
        )
        response.raise_for_status()

        return response.json()["choices"][0]["message"]["content"]

    def _call_openai(
        self, messages: List[Dict], temperature: float, max_tokens: int
    ) -> str:
        """调用OpenAI API"""
        import openai

        client = openai.OpenAI(
            api_key=self.api_key, base_url=self.base_url if self.base_url else None
        )

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content

    def _call_anthropic(
        self, messages: List[Dict], temperature: float, max_tokens: int
    ) -> str:
        """调用Anthropic API"""
        import anthropic

        client = anthropic.Anthropic(api_key=self.api_key)

        # 转换消息格式
        system_msg = ""
        user_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                user_messages.append(msg)

        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_msg,
            messages=user_messages,
        )

        return response.content[0].text


class AICitationMatcher:
    """AI驱动的引用匹配器 - 集成混合检索引擎和上下文理解"""

    def __init__(
        self,
        db_manager: LiteratureDatabaseManager,
        api_manager: AIAPIManager,
        citation_style: str = "author-year",
        max_citations: int = 3,
        min_relevance: float = 0.6,
        batch_size: int = 5,
        top_k_semantic: int = 50,
        weight_recency: int = 50,
        weight_citation: int = 50,
        use_hybrid_search: bool = True,
        search_engine=None,
        research_context=None,
    ):
        """
        初始化AI匹配器

        匹配策略（两步法）：
        1. 先选出语义最相关的前 top_k_semantic 篇（门槛筛选）
        2. 在这 top_k_semantic 篇中，用 weight_recency 和 weight_citation 加权排序

        例如：weight_recency=70, weight_citation=30
        → 优先推荐新文献，但也适当考虑经典高引文献

        Args:
            db_manager: 文献数据库管理器
            api_manager: AI API管理器
            citation_style: 引用风格
            max_citations: 每句话最大引用数
            min_relevance: 最低语义相关性阈值（AI评分门槛）
            batch_size: 批量处理时每批候选文献数
            top_k_semantic: 语义筛选保留的前K篇数量
            weight_recency: 新颖度权重 (%)，与weight_citation之和应为100
            weight_citation: 引用次数权重 (%)，与weight_recency之和应为100
            use_hybrid_search: 是否使用混合检索引擎（默认启用）
            search_engine: 外部传入的搜索引擎实例（可选）
            research_context: 研究上下文（可选，用于更精准的匹配）
        """
        self.db_manager = db_manager
        self.api_manager = api_manager
        self.citation_style = citation_style
        self.max_citations = max_citations
        self.min_relevance = min_relevance
        self.batch_size = batch_size
        self.research_context = research_context
        self.top_k_semantic = top_k_semantic
        self.weight_recency = weight_recency / 100.0
        self.weight_citation = weight_citation / 100.0
        self.use_hybrid_search = use_hybrid_search
        self.search_engine = search_engine

        if use_hybrid_search and search_engine is None:
            try:
                from .search_engine import HybridSearchEngine

                self.search_engine = HybridSearchEngine(
                    db_manager=db_manager,
                    api_manager=api_manager,
                    use_query_expansion=True,
                    use_cross_encoder=True,
                    use_mmr=True,
                    mmr_lambda=0.6,
                    vector_weight=0.4,
                    keyword_weight=0.3,
                    citation_weight=0.3,
                )
                self.search_engine.build_index()
            except Exception as e:
                print(f"混合检索引擎初始化失败，将使用传统检索: {e}")
                self.use_hybrid_search = False
                self.search_engine = None

    def match_for_sentence(
        self, sentence: Sentence, year_range: int = 10
    ) -> List[AIMatchResult]:
        """
        为单个句子AI匹配引用

        Args:
            sentence: 要匹配的句子
            year_range: 年份范围

        Returns:
            匹配结果列表
        """
        import datetime

        current_year = datetime.datetime.now().year
        year_min = current_year - year_range

        # 1. 使用关键词初筛候选文献（减少AI调用成本）
        candidates = self._get_candidates(sentence, year_min)

        if not candidates:
            return []

        # 2. 使用AI进行语义匹配评分
        matches = []

        # 分批处理，每批batch_size篇
        for i in range(0, len(candidates), self.batch_size):
            batch = candidates[i : i + self.batch_size]
            batch_matches = self._ai_match_batch(sentence, batch)
            matches.extend(batch_matches)

        # 3. 第一步筛选：按语义相关性选出前 top_k_semantic 篇
        matches = [m for m in matches if m.relevance_score >= self.min_relevance]
        matches.sort(key=lambda x: x.relevance_score, reverse=True)
        top_semantic_matches = matches[: self.top_k_semantic]

        if not top_semantic_matches:
            return []

        # 4. 第二步排序：在这 top_k_semantic 篇中，用新颖度和引用次数加权排序
        for match in top_semantic_matches:
            # 计算新颖度分数 (0-1)
            recency_score = self._calculate_recency_score(match.paper, current_year)
            # 计算引用次数分数 (0-1)
            citation_score = self._calculate_citation_score(match.paper)

            # 综合分数（不考虑语义，因为已经筛选过了）
            match.composite_score = (
                recency_score * self.weight_recency
                + citation_score * self.weight_citation
            )

            # 更新匹配理由，加入权重信息
            match.relevance_reason = (
                f"语义相关度: {match.relevance_score:.2f} | "
                f"新颖度: {recency_score:.2f} | "
                f"引用影响力: {citation_score:.2f}"
            )

        # 按综合分数排序
        top_semantic_matches.sort(key=lambda x: x.composite_score, reverse=True)

        return top_semantic_matches[: self.max_citations]

    def _get_candidates(
        self,
        sentence: Sentence,
        year_min: int,
        max_candidates: int = 50,
        prioritize_recent: bool = True,
    ) -> List[Paper]:
        """获取候选文献"""
        import datetime

        if self.use_hybrid_search and self.search_engine is not None:
            try:
                current_year = datetime.datetime.now().year
                results = self.search_engine.search_for_sentence(
                    sentence=sentence,
                    top_k=max_candidates,
                    year_range=current_year - year_min,
                )
                return [r.paper for r in results]
            except Exception as e:
                print(f"混合检索失败，回退到传统检索: {e}")

        return self._get_candidates_traditional(
            sentence, year_min, max_candidates, prioritize_recent
        )

    def _get_candidates_traditional(
        self,
        sentence: Sentence,
        year_min: int,
        max_candidates: int = 50,
        prioritize_recent: bool = True,
    ) -> List[Paper]:
        """传统关键词检索（回退方案）"""
        import datetime

        if not sentence.keywords:
            keywords = self._extract_nouns(sentence.text)
        else:
            keywords = sentence.keywords

        if not keywords:
            return self.db_manager.search(
                query="", limit=max_candidates, year_min=year_min, order_by="cited_by"
            )

        current_year = datetime.datetime.now().year
        recent_year_min = max(year_min, current_year - 5)

        recent_results = self.db_manager.search_by_keywords(
            keywords=keywords,
            limit=max_candidates // 2,
            year_min=recent_year_min,
            year_max=current_year,
        )
        recent_papers = [paper for paper, _ in recent_results]

        older_results = self.db_manager.search_by_keywords(
            keywords=keywords,
            limit=max_candidates - len(recent_papers),
            year_min=year_min,
            year_max=recent_year_min - 1,
        )
        older_papers = [paper for paper, _ in older_results]

        all_papers = recent_papers + older_papers

        seen_ids = set()
        unique_papers = []
        for paper in all_papers:
            if paper.id not in seen_ids:
                seen_ids.add(paper.id)
                unique_papers.append(paper)

        return unique_papers[:max_candidates]

    def _extract_nouns(self, text: str) -> List[str]:
        """从文本中提取名词（简化版）"""
        # 简单的启发式规则：长度大于4的单词
        words = re.findall(r"\b[A-Za-z]{4,}\b", text)

        # 停用词过滤
        stopwords = {
            "this",
            "that",
            "with",
            "from",
            "have",
            "were",
            "which",
            "about",
            "their",
            "they",
            "been",
            "than",
            "them",
            "into",
            "just",
            "over",
            "also",
            "only",
            "some",
            "time",
            "very",
            "what",
            "when",
            "where",
            "study",
            "research",
            "paper",
            "result",
            "results",
            "data",
            "analysis",
            "method",
            "methods",
            "used",
            "using",
            "shown",
            "showed",
            "found",
            "observed",
            "indicated",
            "suggested",
        }

        return [w.lower() for w in words if w.lower() not in stopwords][:5]

    def _ai_match_batch(
        self, sentence: Sentence, candidates: List[Paper]
    ) -> List[AIMatchResult]:
        """
        使用AI批量匹配句子与候选文献
        """
        # 构建提示词
        prompt = self._build_matching_prompt(sentence, candidates)

        messages = [
            {
                "role": "system",
                "content": f"""You are an expert academic research assistant specializing in citation matching.

Your task is to evaluate how well each candidate paper can serve as a citation for the given draft sentence.
IMPORTANT: These papers have already passed initial semantic screening. Your job is to (1) infer what the sentence truly needs from a citation, and (2) score each paper accordingly.

For EACH paper, output:
- semantic_score: 0.0-1.0
- publication_year
- citation_count
- confidence: high / medium / low

User's secondary ranking preference (for papers with similar semantic scores):
- Recency (last 5 years): {self.weight_recency * 100:.0f}%
- Citation Count: {self.weight_citation * 100:.0f}%

If semantic score difference > 0.10, prioritize semantic score.
If semantic score difference <= 0.10, apply secondary ranking weights.

SENTENCE-DRIVEN EVALUATION (MANDATORY)

Step 1 - Understand the sentence's citation need
Infer the sentence's role and what evidence it requires. Identify:
A) Sentence function (choose one or more):
- Background framing / importance
- Regional or production statistic
- Specific quantitative claim (percent, emission factor, yield change)
- Mechanistic explanation (process/pathway)
- Management effect / intervention comparison
- Trade-off claim (yield vs emissions / N loss)
- Methodological justification

B) What MUST be matched for this sentence to be properly supported (the "non-negotiables" inferred from the sentence), such as:
- Geographic specificity (e.g., a named region like NCP)
- Crop/cropping system specificity (e.g., wheat-maize rotation)
- Target variable specificity (N2O vs NO vs total N losses vs NUE)
- Mechanism specificity (nitrification/denitrification, fertilizer-derived, indirect emissions)
- Evidence type specificity (field measurement, long-term trend, statistical dataset, modeling)

C) What is OPTIONAL but improves fit (nice-to-have).

Step 2 - Evaluate each paper against the sentence's inferred needs
Score based on how directly the paper provides the required support for the sentence's function and non-negotiables.

When scoring, weigh dimensions ONLY to the extent the sentence demands them:
- Geographic relevance (only critical if the sentence is region-specific)
- Crop/system relevance (only critical if the sentence is crop/system-specific)
- Mechanistic relevance (only critical if the sentence makes mechanistic claims)
- Method/design relevance (only critical if the sentence implies evidence type)
- Quantitative compatibility (critical if the sentence contains specific numbers)

Avoid keyword-matching bias: do not give a high score just because the paper contains similar terms.
Prefer papers that can be cited without extrapolation.
If support would require major extrapolation (different region/system/variable), lower the score.

SCORING GUIDE
0.90-1.00: Direct, clean support for the sentence with minimal extrapolation
0.75-0.89: Strong support; minor mismatch but still credible
0.60-0.74: Acceptable but indirect; some extrapolation needed
0.40-0.59: Weak support; better citations likely exist
0.00-0.39: Not suitable for this sentence

Confidence:
- high: clear direct support
- medium: plausible but indirect
- low: significant inference/extrapolation required

Return ONLY valid JSON. No extra text.""",
            },
            {"role": "user", "content": prompt},
        ]

        try:
            response = self.api_manager.call_model(
                messages=messages, temperature=0.3, max_tokens=2000
            )

            # 解析JSON响应
            results = self._parse_ai_response(response, candidates)
            return results

        except Exception as e:
            print(f"AI匹配失败: {e}")
            # 如果AI调用失败，返回空列表
            return []

    def _build_matching_prompt(
        self, sentence: Sentence, candidates: List[Paper]
    ) -> str:
        """构建AI匹配提示词"""

        prompt_parts = []

        if self.research_context:
            prompt_parts.extend(
                [
                    "=" * 60,
                    "GLOBAL RESEARCH CONTEXT (Important for citation matching)",
                    "=" * 60,
                    f"Manuscript Title: {self.research_context.title or 'N/A'}",
                    f"Research Field: {self.research_context.research_field or 'N/A'}",
                    f"Study Area: {self.research_context.study_area or 'N/A'}",
                    f"Main Focus: {self.research_context.main_focus or 'N/A'}",
                    f"Crops: {', '.join(self.research_context.crops) if self.research_context.crops else 'N/A'}",
                    f"Treatments: {', '.join(self.research_context.treatments) if self.research_context.treatments else 'N/A'}",
                    f"Key Variables: {', '.join(self.research_context.key_variables) if self.research_context.key_variables else 'N/A'}",
                    "=" * 60,
                    "",
                ]
            )

        prompt_parts.extend(
            [
                "Draft Sentence:",
                f'"{sentence.text}"',
                "",
                "Candidate Papers:",
                "",
            ]
        )

        for i, paper in enumerate(candidates, 1):
            prompt_parts.append(f"[{i}] {paper.title}")
            prompt_parts.append(f"    Authors: {paper.authors}")
            prompt_parts.append(f"    Year: {paper.year}")
            prompt_parts.append(
                f"    Abstract: {paper.abstract[:300]}..."
                if len(paper.abstract) > 300
                else f"    Abstract: {paper.abstract}"
            )
            prompt_parts.append("")

        prompt_parts.extend(
            [
                "Evaluate the relevance of each paper to the draft sentence.",
                "",
                "Respond in this exact JSON format:",
                "{",
                '  "evaluations": [',
            ]
        )

        for i in range(1, len(candidates) + 1):
            prompt_parts.append("    {")
            prompt_parts.append(f'      "paper_id": {i},')
            prompt_parts.append('      "relevance_score": 0.85,')
            prompt_parts.append('      "confidence": "high",')
            prompt_parts.append(
                '      "reason": "Brief explanation of why this paper is or is not relevant"'
            )
            prompt_parts.append("    },")

        # 移除最后一个逗号
        prompt_parts[-1] = prompt_parts[-1].rstrip(",")

        prompt_parts.extend(["  ]", "}"])

        return "\n".join(prompt_parts)

    def _parse_ai_response(
        self, response: str, candidates: List[Paper]
    ) -> List[AIMatchResult]:
        """解析AI响应"""
        try:
            # 尝试提取JSON
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(response)

            evaluations = data.get("evaluations", [])

            results = []
            for eval_data in evaluations:
                paper_idx = eval_data.get("paper_id", 0) - 1

                if 0 <= paper_idx < len(candidates):
                    paper = candidates[paper_idx]

                    result = AIMatchResult(
                        paper=paper,
                        relevance_score=float(
                            eval_data.get("semantic_score")
                            or eval_data.get("relevance_score", 0)
                        ),
                        relevance_reason=eval_data.get(
                            "reason", eval_data.get("justification", "")
                        ),
                        confidence=eval_data.get("confidence", "medium"),
                    )
                    results.append(result)

            return results

        except Exception as e:
            print(f"解析AI响应失败: {e}")
            print(f"响应内容: {response}")
            return []

    def batch_match(
        self, sentences: List[Sentence], year_range: int = 10, progress_callback=None
    ) -> List[SentenceWithAICitations]:
        """
        批量匹配多个句子
        """
        results = []
        total = len(sentences)

        for idx, sentence in enumerate(sentences):
            citations = self.match_for_sentence(sentence, year_range)

            result = SentenceWithAICitations(sentence=sentence, citations=citations)
            results.append(result)

            if progress_callback:
                progress_callback(idx + 1, total)

        return results

    def format_citation(self, match: AIMatchResult, index: Optional[int] = None) -> str:
        """格式化引用文本"""
        paper = match.paper

        if self.citation_style == "numbered":
            if index:
                return f"[{index}]"
            else:
                return f"[{paper.id}]"
        else:
            return paper.format_citation(style=self.citation_style)

    def insert_citations_into_text(
        self,
        sentence: Sentence,
        citations: List[AIMatchResult],
        insert_position: str = "end",
    ) -> str:
        """将引用插入到句子文本中"""
        if not citations:
            return sentence.text

        citation_texts = []
        for i, citation in enumerate(citations, 1):
            citation_texts.append(self.format_citation(citation, i))

        if self.citation_style == "numbered":
            combined = (
                "["
                + ", ".join(c.replace("[", "").replace("]", "") for c in citation_texts)
                + "]"
            )
        else:
            combined = "(" + "; ".join(c.strip("()") for c in citation_texts) + ")"

        text = sentence.text
        if insert_position == "end":
            if text.endswith("."):
                return text[:-1] + " " + combined + "."
            else:
                return text + " " + combined
        else:
            return text + " " + combined

    def generate_bibliography(
        self, all_matches: List[SentenceWithAICitations], style: str = "apa"
    ) -> str:
        """生成参考文献列表"""
        # 收集所有使用过的论文（去重）
        used_papers = {}
        for swc in all_matches:
            for citation in swc.citations:
                paper_id = citation.paper.id
                if paper_id not in used_papers:
                    used_papers[paper_id] = citation.paper

        if not used_papers:
            return ""

        # 排序
        sorted_papers = sorted(
            used_papers.values(),
            key=lambda p: (
                p.authors.split(",")[0].strip().split()[-1] if p.authors else ""
            ).lower(),
        )

        references = ["# References\n"]

        for paper in sorted_papers:
            ref = self._format_reference(paper, style)
            references.append(ref)

        return "\n\n".join(references)

    def _format_reference(self, paper: Paper, style: str) -> str:
        """格式化单条参考文献"""
        authors = paper.authors.replace(";", ", ")

        if style == "apa":
            return f"{authors} ({paper.year}). {paper.title}. {paper.journal}, {paper.volume}({paper.issue}), {paper.pages}."
        elif style == "nature":
            return f"{authors}. {paper.title}. {paper.journal} {paper.year}."
        elif style == "vancouver":
            return f"{authors}. {paper.title}. {paper.journal}. {paper.year};{paper.volume}:{paper.pages}."
        elif style == "ieee":
            return f'{authors}, "{paper.title}," {paper.journal}, vol. {paper.volume}, no. {paper.issue}, pp. {paper.pages}, {paper.year}.'
        else:
            return f"{authors}. {paper.title}. {paper.journal} {paper.year};{paper.volume}:{paper.pages}."

    def _calculate_recency_score(self, paper: Paper, current_year: int) -> float:
        """计算文献新颖度分数 (0-1)

        越新的文献分数越高
        """
        if paper.year <= 0:
            return 0.0

        years_ago = current_year - paper.year

        if years_ago <= 2:
            return 1.0  # 最近2年：满分
        elif years_ago <= 5:
            return 0.8  # 3-5年：0.8
        elif years_ago <= 10:
            return 0.6  # 6-10年：0.6
        elif years_ago <= 15:
            return 0.4  # 11-15年：0.4
        elif years_ago <= 20:
            return 0.2  # 16-20年：0.2
        else:
            return 0.1  # 20年以上：0.1（经典文献也有价值）

    def _calculate_citation_score(self, paper: Paper) -> float:
        """计算引用影响力分数 (0-1)

        基于引用次数，使用对数缩放
        """
        import math

        if paper.cited_by <= 0:
            return 0.0

        # 使用对数缩放，避免高引用文献垄断
        # 100次引用 = 0.4分，1000次 = 0.7分，10000次 = 1.0分
        score = min(1.0, math.log10(paper.cited_by) / 4)
        return score
