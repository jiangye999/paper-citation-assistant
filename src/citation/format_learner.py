"""
参考文献格式学习模块
通过AI学习用户提供的参考文献格式示例
"""

import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ReferenceFormat:
    """参考文献格式"""

    name: str = "default"  # 格式名称
    template: str = ""  # AI学习的格式模板
    example: str = ""  # 用户提供的示例
    format_rules: str = ""  # AI总结的格式规则


class ReferenceFormatLearner:
    """参考文献格式学习器"""

    def __init__(self, api_manager=None):
        self.api_manager = api_manager
        self.format_cache: Optional[ReferenceFormat] = None

    def learn_from_example(self, example_text: str) -> ReferenceFormat:
        """
        从用户提供的示例中学习格式

        Args:
            example_text: 用户提供的参考文献示例

        Returns:
            学习到的格式
        """
        if not self.api_manager:
            # 如果没有API管理器，返回默认格式
            return ReferenceFormat(
                name="default",
                template="{authors} ({year}). {title}. {journal}, {volume}({issue}), {pages}.",
                example=example_text,
            )

        # 使用AI分析格式
        prompt = f"""Analyze the following reference format example and extract the formatting rules:

Example:
{example_text}

Please analyze:
1. Author format (e.g., "Smith, J.", "Smith, J., & Jones, M.", "Smith et al.")
2. Year format (e.g., "(2024)", "2024", "[2024]")
3. Title formatting (e.g., italics, capitalization style)
4. Journal name formatting (e.g., full name, abbreviation, italics)
5. Volume/issue formatting (e.g., "vol. 12, no. 3", "12(3)", "12: ")
6. Page formatting (e.g., "pp. 123-145", "123-145", "123--145")
7. Punctuation and spacing patterns
8. Order of elements

Respond in this exact format:
FORMAT_NAME: [Name of the format style, e.g., APA, Nature, Vancouver]

TEMPLATE: [Create a template with placeholders like {{authors}}, {{year}}, {{title}}, {{journal}}, {{volume}}, {{issue}}, {{pages}}, {{doi}}]

RULES:
1. [Rule 1]
2. [Rule 2]
...
"""

        messages = [
            {
                "role": "system",
                "content": "You are an expert in academic citation styles. Analyze reference formats precisely.",
            },
            {"role": "user", "content": prompt},
        ]

        try:
            response = self.api_manager.call_model(
                messages, temperature=0.3, max_tokens=1000
            )

            # 解析响应
            format_name = self._extract_section(response, "FORMAT_NAME")
            template = self._extract_section(response, "TEMPLATE")
            rules = self._extract_section(response, "RULES")

            ref_format = ReferenceFormat(
                name=format_name or "custom",
                template=template or self._get_default_template(),
                example=example_text,
                format_rules=rules,
            )

            self.format_cache = ref_format
            return ref_format

        except Exception as e:
            print(f"格式学习失败: {e}")
            # 返回默认格式
            return ReferenceFormat(
                name="default",
                template=self._get_default_template(),
                example=example_text,
            )

    def _extract_section(self, text: str, section_name: str) -> str:
        """从AI响应中提取特定部分"""
        pattern = rf"{section_name}:?\s*\n?(.*?)(?=\n\w+:|$)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""

    def _get_default_template(self) -> str:
        """获取默认模板"""
        return "{authors} ({year}). {title}. {journal}, {volume}({issue}), {pages}."

    def format_reference(
        self, paper, ref_format: Optional[ReferenceFormat] = None
    ) -> str:
        """
        根据学习的格式格式化单条参考文献

        Args:
            paper: Paper对象
            ref_format: 参考文献格式，如果为None使用缓存的格式

        Returns:
            格式化后的参考文献文本
        """
        if ref_format is None:
            ref_format = self.format_cache

        if ref_format is None or not ref_format.template:
            # 使用默认APA格式
            return self._format_apa(paper)

        # 使用AI根据模板和规则格式化
        if self.api_manager:
            return self._format_with_ai(paper, ref_format)
        else:
            return self._format_with_template(paper, ref_format.template)

    def _format_apa(self, paper) -> str:
        """默认APA格式"""
        authors = paper.authors.replace(";", ", ")
        return f"{authors} ({paper.year}). {paper.title}. {paper.journal}, {paper.volume}({paper.issue}), {paper.pages}."

    def _format_with_template(self, paper, template: str) -> str:
        """使用简单模板替换格式化"""
        try:
            return template.format(
                authors=paper.authors.replace(";", ", "),
                year=paper.year,
                title=paper.title,
                journal=paper.journal,
                volume=paper.volume,
                issue=paper.issue,
                pages=paper.pages,
                doi=paper.doi,
            )
        except:
            # 如果模板格式化失败，返回APA格式
            return self._format_apa(paper)

    def _format_with_ai(self, paper, ref_format: ReferenceFormat) -> str:
        """使用AI根据学习的格式格式化"""
        prompt = f"""Format the following paper according to the learned reference style:

Format Rules:
{ref_format.format_rules}

Template:
{ref_format.template}

Example:
{ref_format.example}

Paper to format:
- Authors: {paper.authors}
- Year: {paper.year}
- Title: {paper.title}
- Journal: {paper.journal}
- Volume: {paper.volume}
- Issue: {paper.issue}
- Pages: {paper.pages}
- DOI: {paper.doi}

Respond ONLY with the formatted reference, no additional text."""

        messages = [
            {
                "role": "system",
                "content": "You are an expert in academic citation formatting. Apply the learned format precisely.",
            },
            {"role": "user", "content": prompt},
        ]

        try:
            response = self.api_manager.call_model(
                messages, temperature=0.3, max_tokens=300
            )
            return response.strip()
        except Exception as e:
            print(f"AI格式化失败: {e}")
            return self._format_with_template(paper, ref_format.template)

    def batch_format(
        self, papers: List, ref_format: Optional[ReferenceFormat] = None
    ) -> List[str]:
        """
        批量格式化参考文献

        Args:
            papers: Paper对象列表
            ref_format: 参考文献格式

        Returns:
            格式化后的参考文献列表
        """
        if ref_format is None:
            ref_format = self.format_cache

        formatted_refs = []
        for paper in papers:
            ref = self.format_reference(paper, ref_format)
            formatted_refs.append(ref)

        return formatted_refs
