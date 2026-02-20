"""
文档上下文理解模块
在匹配引用前，先通读全文理解研究背景、实验设计等上下文信息
"""

import os
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from ..literature.db_manager import LiteratureDatabaseManager
from ..draft.analyzer import DraftAnalysisResult


@dataclass
class ResearchContext:
    """研究上下文"""

    title: str = ""
    research_field: str = ""  # 研究领域
    study_object: str = ""  # 研究对象
    study_area: str = ""  # 研究区域/地点
    methods: List[str] = field(default_factory=list)  # 研究方法
    crops: List[str] = field(default_factory=list)  # 涉及的作物
    treatments: List[str] = field(default_factory=list)  # 处理/实验条件
    key_variables: List[str] = field(default_factory=list)  # 关键变量
    main_focus: str = ""  # 主要研究焦点
    additional_context: str = ""  # 其他重要背景


class DocumentContextAnalyzer:
    """文档上下文分析器 - 理解全文背景后生成上下文文件"""

    def __init__(self, api_manager, output_dir: str = "output"):
        self.api_manager = api_manager
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def analyze(
        self,
        draft_result: DraftAnalysisResult,
        output_filename: str = "research_context.md",
    ) -> ResearchContext:
        """
        分析文档，生成研究上下文

        Args:
            draft_result: 文档分析结果
            output_filename: 输出的上下文文件名

        Returns:
            ResearchContext 对象
        """
        # 构建分析提示词
        prompt = self._build_context_prompt(draft_result)

        messages = [
            {
                "role": "system",
                "content": """You are an expert academic research assistant specialized in understanding scientific manuscripts.
Your task is to analyze the full text of a research paper/manuscript and extract key contextual information that will help with citation matching.

Extract the following information in detail:
1. Research field (e.g., agronomy, environmental science, soil science)
2. Study object (e.g., maize, wheat, nitrogen cycling)
3. Study area/location (e.g., North China Plain, Hebei Province)
4. Research methods (e.g., field experiment, modeling, laboratory incubation)
5. Crops involved (e.g., maize, wheat, rice)
6. Experimental treatments/conditions (e.g., nitrogen fertilization rates, tillage methods)
7. Key variables measured (e.g., N2O emission, yield, nitrogen use efficiency)
8. Main research focus/objective

Be very specific. For location, include country and region if mentioned.
For methods, list all techniques used.
For treatments, include specific levels if mentioned (e.g., 200 kg N/ha).

Respond ONLY in valid JSON format with no additional text.""",
            },
            {"role": "user", "content": prompt},
        ]

        try:
            # 调用 AI 分析
            response = self.api_manager.call_model(
                messages=messages, temperature=0.3, max_tokens=2000
            )

            # 解析 JSON 响应
            context = self._parse_response(response)

            # 生成 Markdown 文件
            self._save_context_md(context, output_filename, draft_result.title)

            return context

        except Exception as e:
            print(f"上下文分析失败: {e}")
            # 返回空上下文
            return ResearchContext(title=draft_result.title)

    def _build_context_prompt(self, draft_result: DraftAnalysisResult) -> str:
        """构建分析提示词"""
        prompt_parts = [
            "Please analyze the following manuscript and extract contextual information:",
            "",
            "=== Title ===",
            draft_result.title or "(No title found)",
            "",
            "=== Full Text ===",
            draft_result.full_text[:8000],  # 限制长度
            "",
            "Extract the research context in JSON format.",
        ]
        return "\n".join(prompt_parts)

    def _parse_response(self, response: str) -> ResearchContext:
        """解析 AI 响应"""
        try:
            # 提取 JSON
            import re

            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(response)

            return ResearchContext(
                title=data.get("title", ""),
                research_field=data.get("research_field", ""),
                study_object=data.get("study_object", ""),
                study_area=data.get("study_area", ""),
                methods=data.get("methods", []),
                crops=data.get("crops", []),
                treatments=data.get("treatments", []),
                key_variables=data.get("key_variables", []),
                main_focus=data.get("main_focus", ""),
                additional_context=data.get("additional_context", ""),
            )
        except Exception as e:
            print(f"解析上下文失败: {e}")
            return ResearchContext()

    def _save_context_md(self, context: ResearchContext, filename: str, title: str):
        """保存为 Markdown 文件"""
        md_content = f"""# 研究上下文背景

> 本文件由 AI 自动生成，用于辅助文献引用匹配

## 基本信息

- **标题**: {title}
- **研究领域**: {context.research_field}
- **研究对象**: {context.study_object}
- **研究区域**: {context.study_area}

## 研究方法

{chr(10).join(f"- {m}" for m in context.methods) if context.methods else "- 未识别"}

## 作物信息

{chr(10).join(f"- {c}" for c in context.crops) if context.crops else "- 未识别"}

## 实验处理/条件

{chr(10).join(f"- {t}" for t in context.treatments) if context.treatments else "- 未识别"}

## 关键变量

{chr(10).join(f"- {v}" for v in context.key_variables) if context.key_variables else "- 未识别"}

## 主要研究焦点

{context.main_focus or "未识别"}

## 其他背景信息

{context.additional_context or "无"}

---
*此文件在文献匹配时会被参考，以确保引用的相关性和准确性*
"""

        output_path = self.output_dir / filename
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        print(f"上下文文件已生成: {output_path}")

    def load_context(
        self, filename: str = "research_context.md"
    ) -> Optional[ResearchContext]:
        """加载已有的上下文文件"""
        output_path = self.output_dir / filename

        if not output_path.exists():
            return None

        # 简单解析（也可以存储为 JSON 方便读取）
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 简单提取（实际可以用更复杂的解析）
            context = ResearchContext()
            context.title = (
                title if (title := self._extract_section(content, "标题")) else ""
            )
            context.research_field = self._extract_section(content, "研究领域")
            context.study_area = self._extract_section(content, "研究区域")
            context.main_focus = self._extract_section(content, "主要研究焦点")

            return context
        except:
            return None

    def _extract_section(self, content: str, section_name: str) -> str:
        """提取 Markdown 中的章节内容"""
        import re

        pattern = rf"\*\*{section_name}\*\*:\s*(.+?)(?=\n\*\*|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        return match.group(1).strip() if match else ""


def build_context_prompt_with_reference(
    sentence_text: str, context: ResearchContext
) -> str:
    """
    构建带上下文的匹配提示词

    Args:
        sentence_text: 当前句子
        context: 研究上下文

    Returns:
        增强的提示词
    """
    context_info = f"""
=== GLOBAL RESEARCH CONTEXT (Important for citation matching) ===

This manuscript is about: {context.main_focus}
Study area: {context.study_area}
Crops involved: {", ".join(context.crops) if context.crops else "Not specified"}
Treatments/conditions: {", ".join(context.treatments) if context.treatments else "Not specified"}
Key variables: {", ".join(context.key_variables) if context.key_variables else "Not specified"}

When evaluating citation relevance, consider:
1. Is the paper relevant to this specific study context?
2. Does it address the same geographic area?
3. Does it study similar crops and treatments?
4. Are the key variables related?

=== CURRENT SENTENCE TO BE CITED ===
{sentence_text}
"""
    return context_info
