from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..literature.db_manager import LiteratureDatabaseManager, Paper
from ..draft.analyzer import Sentence


@dataclass
class CitationMatch:
    """引用匹配结果"""

    paper: Paper
    relevance_score: float  # 相关性分数 0.0-1.0
    match_reason: str = ""  # 匹配原因说明


@dataclass
class SentenceWithCitations:
    """带引用的句子"""

    sentence: Sentence
    citations: List[CitationMatch] = field(default_factory=list)
    suggested_keywords: List[str] = field(default_factory=list)


class CitationMatcher:
    """引用匹配器 - 为句子匹配相关文献"""

    def __init__(
        self,
        db_manager: LiteratureDatabaseManager,
        citation_style: str = "author-year",
        max_citations: int = 3,
        min_relevance: float = 0.3,
    ):
        """
        初始化匹配器

        Args:
            db_manager: 文献数据库管理器
            citation_style: 引用风格
            max_citations: 每句话最大引用数
            min_relevance: 最低相关性阈值
        """
        self.db_manager = db_manager
        self.citation_style = citation_style
        self.max_citations = max_citations
        self.min_relevance = min_relevance

        # TF-IDF向量化器（用于语义相似度计算）
        self.vectorizer = TfidfVectorizer(
            max_features=5000, stop_words="english", ngram_range=(1, 2)
        )

    def match_for_sentence(
        self, sentence: Sentence, year_range: int = 10
    ) -> List[CitationMatch]:
        """
        为单个句子匹配引用

        Args:
            sentence: 要匹配的句子
            year_range: 年份范围（当前年份往前）

        Returns:
            匹配结果列表
        """
        if not sentence.keywords:
            return []

        # 计算年份范围
        import datetime

        current_year = datetime.datetime.now().year
        year_min = current_year - year_range

        # 1. 基于关键词搜索
        keyword_results = self.db_manager.search_by_keywords(
            keywords=sentence.keywords,
            limit=self.max_citations * 3,  # 获取更多以便筛选
            year_min=year_min,
        )

        if not keyword_results:
            return []

        # 2. 计算语义相似度
        matches = []
        for paper, keyword_score in keyword_results:
            # 计算综合分数
            semantic_score = self._calculate_semantic_similarity(sentence.text, paper)

            # 计算质量分数
            quality_score = self._calculate_quality_score(paper)

            # 综合分数（可调整权重）
            combined_score = (
                keyword_score * 0.4 + semantic_score * 0.4 + quality_score * 0.2
            )

            if combined_score >= self.min_relevance:
                match = CitationMatch(
                    paper=paper,
                    relevance_score=combined_score,
                    match_reason=self._generate_match_reason(paper, sentence),
                )
                matches.append(match)

        # 3. 按分数排序并限制数量
        matches.sort(key=lambda x: x.relevance_score, reverse=True)
        return matches[: self.max_citations]

    def batch_match(
        self, sentences: List[Sentence], year_range: int = 10, progress_callback=None
    ) -> List[SentenceWithCitations]:
        """
        批量匹配多个句子

        Args:
            sentences: 句子列表
            year_range: 年份范围
            progress_callback: 进度回调函数(current, total)

        Returns:
            带引用的句子列表
        """
        results = []
        total = len(sentences)

        for idx, sentence in enumerate(sentences):
            citations = self.match_for_sentence(sentence, year_range)

            result = SentenceWithCitations(
                sentence=sentence,
                citations=citations,
                suggested_keywords=sentence.keywords,
            )
            results.append(result)

            if progress_callback:
                progress_callback(idx + 1, total)

        return results

    def _calculate_semantic_similarity(self, text: str, paper: Paper) -> float:
        """
        计算文本与论文的语义相似度

        Args:
            text: 输入文本
            paper: 论文对象

        Returns:
            相似度分数 0.0-1.0
        """
        # 构建论文文本
        paper_text = f"{paper.title} {paper.abstract} {paper.keywords}"

        if not paper_text.strip():
            return 0.0

        try:
            # 使用TF-IDF计算相似度
            tfidf_matrix = self.vectorizer.fit_transform([text, paper_text])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity)
        except:
            # 如果失败，使用简单匹配
            return self._simple_similarity(text, paper_text)

    def _simple_similarity(self, text1: str, text2: str) -> float:
        """简单的相似度计算（备用方案）"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def _calculate_quality_score(self, paper: Paper) -> float:
        """
        计算论文质量分数

        考虑：
        - 引用次数
        - 发表年份（越新越好，但有上限）
        """
        import datetime

        score = 0.0

        # 引用次数分数 (0-0.6)
        if paper.cited_by > 0:
            # 使用对数缩放
            import math

            citation_score = min(0.6, math.log10(paper.cited_by + 1) / 5)
            score += citation_score

        # 年份分数 (0-0.4)
        if paper.year > 0:
            current_year = datetime.datetime.now().year
            years_ago = current_year - paper.year

            if years_ago <= 2:
                score += 0.4  # 最新
            elif years_ago <= 5:
                score += 0.3
            elif years_ago <= 10:
                score += 0.2
            elif years_ago <= 20:
                score += 0.1
            else:
                score += 0.05  # 经典文献

        return score

    def _generate_match_reason(self, paper: Paper, sentence: Sentence) -> str:
        """生成匹配原因说明"""
        reasons = []

        # 检查关键词匹配
        matched_keywords = []
        for kw in sentence.keywords:
            if (
                kw.lower() in paper.title.lower()
                or kw.lower() in paper.abstract.lower()
                or (paper.keywords and kw.lower() in paper.keywords.lower())
            ):
                matched_keywords.append(kw)

        if matched_keywords:
            reasons.append(f"关键词匹配: {', '.join(matched_keywords[:3])}")

        # 引用次数
        if paper.cited_by > 100:
            reasons.append(f"高引用 ({paper.cited_by}次)")

        # 期刊
        if paper.journal:
            reasons.append(f"发表于{paper.journal}")

        return "; ".join(reasons) if reasons else "语义相关"

    def format_citation(self, match: CitationMatch, index: Optional[int] = None) -> str:
        """
        格式化引用文本

        Args:
            match: 引用匹配结果
            index: 编号（用于numbered格式）

        Returns:
            格式化后的引用文本
        """
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
        citations: List[CitationMatch],
        insert_position: str = "end",  # "end" 或 "before_period"
    ) -> str:
        """
        将引用插入到句子文本中

        Args:
            sentence: 原始句子
            citations: 引用列表
            insert_position: 插入位置

        Returns:
            插入引用后的文本
        """
        if not citations:
            return sentence.text

        # 格式化所有引用
        citation_texts = []
        for i, citation in enumerate(citations, 1):
            citation_texts.append(self.format_citation(citation, i))

        # 组合引用
        if self.citation_style == "numbered":
            combined = (
                "["
                + ", ".join(c.replace("[", "").replace("]", "") for c in citation_texts)
                + "]"
            )
        else:
            combined = "(" + "; ".join(c.strip("()") for c in citation_texts) + ")"

        # 插入位置
        text = sentence.text
        if insert_position == "end":
            # 在句号前插入
            if text.endswith("."):
                return text[:-1] + " " + combined + "."
            else:
                return text + " " + combined
        else:
            # 在句中插入（简化处理：在末尾）
            return text + " " + combined

    def generate_bibliography(
        self, all_matches: List[SentenceWithCitations], style: str = "apa"
    ) -> str:
        """
        生成参考文献列表

        Args:
            all_matches: 所有匹配结果
            style: 参考文献格式

        Returns:
            参考文献文本
        """
        # 收集所有使用过的论文（去重）
        used_papers = {}
        for swc in all_matches:
            for citation in swc.citations:
                paper_id = citation.paper.id
                if paper_id not in used_papers:
                    used_papers[paper_id] = citation.paper

        if not used_papers:
            return ""

        # 排序（按第一作者姓氏）
        sorted_papers = sorted(
            used_papers.values(),
            key=lambda p: (
                p.authors.split(",")[0].strip().split()[-1] if p.authors else ""
            ).lower(),
        )

        # 生成参考文献
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
            # 默认格式
            return f"{authors}. {paper.title}. {paper.journal} {paper.year};{paper.volume}:{paper.pages}."
