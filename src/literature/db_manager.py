"""
文献数据库管理模块
支持Web of Science导出的Plain Text格式导入
"""

import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


@dataclass
class Paper:
    """论文数据类"""

    id: Optional[int] = None
    wos_id: str = ""
    title: str = ""
    authors: str = ""
    journal: str = ""
    year: int = 0
    volume: str = ""
    issue: str = ""
    pages: str = ""
    doi: str = ""
    abstract: str = ""
    keywords: str = ""
    cited_by: int = 0
    research_area: str = ""
    citekey: str = ""  # 格式: Author2025

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "wos_id": self.wos_id,
            "title": self.title,
            "authors": self.authors,
            "journal": self.journal,
            "year": self.year,
            "volume": self.volume,
            "issue": self.issue,
            "pages": self.pages,
            "doi": self.doi,
            "abstract": self.abstract,
            "keywords": self.keywords,
            "cited_by": self.cited_by,
            "research_area": self.research_area,
            "citekey": self.citekey,
        }

    def generate_citekey(self) -> str:
        """
        生成标准citekey格式: AuthorYYYY
        例如: Zhang2025, Smith2023
        """
        # 提取第一作者姓氏
        first_author_lastname = ""
        if self.authors:
            # 尝试多种格式
            if ";" in self.authors:
                first_author = self.authors.split(";")[0].strip()
            elif "," in self.authors:
                first_author = self.authors.split(",")[0].strip()
            elif " and " in self.authors:
                first_author = self.authors.split(" and ")[0].strip()
            else:
                first_author = self.authors.strip()

            # 提取姓氏
            if "," in first_author:
                parts = first_author.split(",")
                first_author_lastname = parts[0].strip()
            else:
                parts = first_author.split()
                if parts:
                    first_author_lastname = parts[-1]

        # 清理姓氏，只保留字母
        first_author_lastname = re.sub(r"[^a-zA-Z]", "", first_author_lastname)
        first_author_lastname = first_author_lastname[:15]

        if not first_author_lastname:
            first_author_lastname = "Unknown"

        first_author_lastname = first_author_lastname.capitalize()

        # 组合为 citekey
        if self.year > 0:
            return f"{first_author_lastname}{self.year}"
        else:
            return f"{first_author_lastname}"

    def format_citation(self, style: str = "author-year") -> str:
        """生成文中引用格式"""
        key = self.citekey or self.generate_citekey()

        if style == "numbered":
            return f"[{self.id}]"
        else:
            # 作者-年份格式
            first_author = "Unknown"
            if self.authors:
                parts = self.authors.split(",")[0].split(";")[0].strip().split()
                if parts:
                    first_author = parts[-1]

            if self.year > 0:
                return f"({first_author} et al., {self.year})"
            else:
                return f"({first_author} et al.)"

    def to_bibtex(self) -> str:
        """生成BibTeX格式条目"""
        citekey = self.citekey or self.generate_citekey()
        title = self.title.replace("{", "").replace("}", "").replace("\n", " ")
        authors = self.authors.replace(";", " and ")

        return f"""@article{{{citekey},
  author = {{{authors}}},
  title = {{{title}}},
  journal = {{{self.journal}}},
  year = {{{self.year}}},
  volume = {{{self.volume}}},
  number = {{{self.issue}}},
  pages = {{{self.pages}}},
  doi = {{{self.doi}}}
}}"""


class LiteratureDatabaseManager:
    """文献数据库管理器"""

    def __init__(self, db_path: str = "data/literature.db"):
        """
        初始化管理器

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self) -> None:
        """初始化数据库表结构"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # 论文表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wos_id TEXT UNIQUE,
                title TEXT NOT NULL,
                authors TEXT,
                journal TEXT,
                year INTEGER,
                volume TEXT,
                issue TEXT,
                pages TEXT,
                doi TEXT UNIQUE,
                abstract TEXT,
                keywords TEXT,
                cited_by INTEGER DEFAULT 0,
                research_area TEXT,
                citekey TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_year ON papers(year)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_journal ON papers(journal)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_doi ON papers(doi)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_keywords ON papers(keywords)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_citekey ON papers(citekey)")

        # 创建全文搜索虚拟表（如果支持）
        try:
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS papers_fts USING fts5(
                    title, abstract, keywords,
                    content='papers',
                    content_rowid='id'
                )
            """)
        except sqlite3.OperationalError:
            # 如果不支持fts5，忽略错误
            pass

        conn.commit()
        conn.close()

    def import_from_wos_txt(self, txt_path: str) -> Tuple[int, List[str]]:
        """
        从Web of Science导出的Plain Text .txt文件导入

        Args:
            txt_path: TXT文件路径

        Returns:
            (导入的论文数量, 错误信息列表)
        """
        import hashlib

        errors = []

        # 读取文件内容
        try:
            with open(txt_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            return 0, [f"读取文件失败: {str(e)}"]

        # 按 ER 切分记录
        records = content.split("\nER\n")

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        count = 0

        for record in records:
            if not record.strip():
                continue

            try:
                # 解析各字段
                paper_id = self._extract_field(record, "UT")
                doi = self._extract_field(record, "DI")
                title = self._extract_field(record, "TI")
                abstract = self._extract_field(record, "AB")
                year_str = self._extract_field(record, "PY")

                # 提取作者
                authors_raw = self._extract_all_fields(record, "AU")
                authors_full = self._extract_all_fields(record, "AF")

                if authors_full:
                    authors = "; ".join(authors_full)
                elif authors_raw:
                    authors = "; ".join(authors_raw)
                else:
                    authors = ""

                # 解析第一作者姓氏
                first_author = ""
                if authors_raw:
                    first_author = authors_raw[0].split(",")[0].strip()
                elif authors:
                    first_author = authors.split(",")[0].strip().split()[-1]

                # 年份处理
                year = 0
                if year_str:
                    try:
                        year = int(year_str[:4])
                    except (ValueError, TypeError):
                        year = 0

                # 生成paper_id
                if paper_id:
                    paper_id_value = f"wos:{paper_id}"
                elif doi:
                    paper_id_value = f"doi:{doi}"
                else:
                    title_hash = hashlib.md5(f"{title}{year}".encode()).hexdigest()[:16]
                    paper_id_value = f"hash:{title_hash}"

                # 清洗摘要
                abstract_cleaned = self._clean_abstract(abstract)

                # 提取其他字段
                journal = self._extract_field(record, "SO")
                volume = self._extract_field(record, "VL")
                issue = self._extract_field(record, "IS")
                pages = self._extract_field(record, "BP", "")
                end_page = self._extract_field(record, "EP", "")
                if pages and end_page:
                    pages = f"{pages}-{end_page}"
                keywords = self._extract_field(record, "DE", "")
                research_area = self._extract_field(record, "SC", "")
                cited_by_str = self._extract_field(record, "TC", "0")
                try:
                    cited_by = int(cited_by_str) if cited_by_str else 0
                except ValueError:
                    cited_by = 0

                # 生成citekey
                temp_paper = Paper(
                    authors=authors,
                    year=year,
                    title=title,
                )
                citekey = temp_paper.generate_citekey()

                # 插入数据库
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO papers 
                    (wos_id, title, authors, journal, year, volume, issue, pages, 
                     doi, abstract, keywords, cited_by, research_area, citekey)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        paper_id_value[:100],
                        title[:500] if title else "",
                        authors[:1000] if authors else "",
                        journal[:200] if journal else "",
                        year,
                        volume[:50] if volume else "",
                        issue[:50] if issue else "",
                        pages[:50] if pages else "",
                        doi[:100] if doi else "",
                        abstract_cleaned[:5000] if abstract_cleaned else "",
                        keywords[:500] if keywords else "",
                        cited_by,
                        research_area[:100] if research_area else "",
                        citekey,
                    ),
                )
                count += 1

            except Exception as e:
                errors.append(f"导入论文失败: {str(e)[:100]}")
                continue

        conn.commit()
        conn.close()

        return count, errors

    def _extract_field(self, record: str, field: str, default: str = "") -> str:
        """从记录中提取单个字段值"""
        pattern = rf"\n{field}\s+(.+?)(?=\n[A-Z]{{2}}\s+|\Z)"
        match = re.search(pattern, record, re.DOTALL)

        if match:
            value = match.group(1).strip()
            value = re.sub(r"\s+", " ", value)
            return value

        if record.startswith(f"{field} "):
            lines = record.split("\n")
            first_line = lines[0][len(field) + 1 :].strip()
            return re.sub(r"\s+", " ", first_line)

        return default

    def _extract_all_fields(self, record: str, field: str) -> List[str]:
        """从记录中提取所有匹配的字段值"""
        values = []
        pattern = rf"\n{field}\s+(.+?)(?=\n[A-Z]{{2}}\s+|\Z)"
        matches = re.findall(pattern, record, re.DOTALL)

        for match in matches:
            value = match.strip()
            values.append(value)

        lines = record.split("\n")
        for line in lines:
            if line.startswith(f"{field} "):
                value = line[len(field) + 1 :].strip()
                if value and value not in values:
                    values.append(value)

        return values

    def _clean_abstract(self, abstract: str) -> str:
        """清洗摘要"""
        if not abstract:
            return ""

        cleaned = abstract.replace("\n", " ")
        cleaned = re.sub(r" +", " ", cleaned)
        cleaned = cleaned.strip()

        return cleaned

    def search(
        self,
        query: str,
        limit: int = 20,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        journal: Optional[str] = None,
        cited_by_min: int = 0,
        order_by: str = "relevance",
    ) -> List[Paper]:
        """
        搜索论文

        Args:
            query: 搜索关键词
            limit: 返回数量限制
            year_min: 最早年份
            year_max: 最晚年份
            journal: 期刊名称过滤
            cited_by_min: 最少引用数
            order_by: 排序字段 (year, cited_by, relevance)

        Returns:
            匹配的论文列表
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        sql = """
            SELECT id, wos_id, title, authors, journal, year, volume, issue, 
                   pages, doi, abstract, keywords, cited_by, research_area, citekey
            FROM papers 
            WHERE (title LIKE ? OR abstract LIKE ? OR keywords LIKE ?)
        """
        params = [f"%{query}%", f"%{query}%", f"%{query}%"]

        if year_min:
            sql += " AND year >= ?"
            params.append(str(year_min))
        if year_max:
            sql += " AND year <= ?"
            params.append(str(year_max))
        if journal:
            sql += " AND journal LIKE ?"
            params.append(f"%{journal}%")
        if cited_by_min > 0:
            sql += " AND cited_by >= ?"
            params.append(str(cited_by_min))

        # 排序
        if order_by == "cited_by":
            sql += " ORDER BY cited_by DESC"
        elif order_by == "year":
            sql += " ORDER BY year DESC"
        else:
            sql += " ORDER BY cited_by DESC, year DESC"

        sql += f" LIMIT {limit}"

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_paper(row) for row in rows]

    def search_by_keywords(
        self,
        keywords: List[str],
        limit: int = 20,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
    ) -> List[Tuple[Paper, float]]:
        """
        根据关键词列表搜索，返回带相关性分数的结果

        Args:
            keywords: 关键词列表
            limit: 返回数量限制
            year_min: 最早年份
            year_max: 最晚年份

        Returns:
            [(论文, 相关性分数), ...]
        """
        if not keywords:
            return []

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # 构建查询条件
        conditions = []
        params = []

        for keyword in keywords:
            conditions.append("(title LIKE ? OR abstract LIKE ? OR keywords LIKE ?)")
            params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])

        sql = f"""
            SELECT id, wos_id, title, authors, journal, year, volume, issue, 
                   pages, doi, abstract, keywords, cited_by, research_area, citekey
            FROM papers 
            WHERE ({" OR ".join(conditions)})
        """

        if year_min:
            sql += " AND year >= ?"
            params.append(year_min)
        if year_max:
            sql += " AND year <= ?"
            params.append(year_max)

        sql += f" ORDER BY cited_by DESC LIMIT {limit * 3}"  # 获取更多以便评分

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()

        # 计算相关性分数
        results = []
        for row in rows:
            paper = self._row_to_paper(row)
            score = self._calculate_relevance_score(paper, keywords)
            results.append((paper, score))

        # 按分数排序并限制数量
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def _calculate_relevance_score(self, paper: Paper, keywords: List[str]) -> float:
        """
        计算论文与关键词的相关性分数

        Returns:
            0.0-1.0之间的分数
        """
        if not keywords:
            return 0.0

        text = f"{paper.title} {paper.abstract} {paper.keywords}".lower()
        matched_keywords = sum(1 for kw in keywords if kw.lower() in text)

        # 基础分数：匹配的关键词比例
        base_score = matched_keywords / len(keywords)

        # 标题匹配加分
        title_bonus = 0.0
        for kw in keywords:
            if kw.lower() in paper.title.lower():
                title_bonus += 0.1

        # 关键词字段匹配加分
        keyword_bonus = 0.0
        for kw in keywords:
            if paper.keywords and kw.lower() in paper.keywords.lower():
                keyword_bonus += 0.05

        score = min(1.0, base_score + title_bonus + keyword_bonus)
        return score

    def _row_to_paper(self, row: Tuple) -> Paper:
        """将数据库行转换为Paper对象"""
        return Paper(
            id=row[0],
            wos_id=row[1],
            title=row[2],
            authors=row[3],
            journal=row[4],
            year=row[5],
            volume=row[6],
            issue=row[7],
            pages=row[8],
            doi=row[9],
            abstract=row[10],
            keywords=row[11],
            cited_by=row[12],
            research_area=row[13],
            citekey=row[14] if len(row) > 14 else "",
        )

    def get_all_papers(self, limit: int = 1000) -> List[Paper]:
        """获取所有论文"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, wos_id, title, authors, journal, year, volume, issue, 
                   pages, doi, abstract, keywords, cited_by, research_area, citekey
            FROM papers ORDER BY cited_by DESC LIMIT ?
        """,
            (limit,),
        )
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_paper(row) for row in rows]

    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        stats = {}

        # 总论文数
        cursor.execute("SELECT COUNT(*) FROM papers")
        stats["total_papers"] = cursor.fetchone()[0]

        # 年份分布
        cursor.execute(
            "SELECT year, COUNT(*) FROM papers WHERE year > 0 GROUP BY year ORDER BY year"
        )
        stats["year_distribution"] = dict(cursor.fetchall())

        # 期刊分布
        cursor.execute(
            'SELECT journal, COUNT(*) FROM papers WHERE journal != "" GROUP BY journal ORDER BY COUNT(*) DESC LIMIT 10'
        )
        stats["top_journals"] = dict(cursor.fetchall())

        # 高引用论文
        cursor.execute(
            "SELECT title, cited_by FROM papers ORDER BY cited_by DESC LIMIT 5"
        )
        stats["top_cited"] = [
            {"title": r[0], "cited_by": r[1]} for r in cursor.fetchall()
        ]

        conn.close()

        return stats

    def clear_database(self) -> None:
        """清空数据库"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM papers")
        conn.commit()
        conn.close()

    def close(self) -> None:
        """关闭数据库连接（预留）"""
        pass


def create_literature_database(
    txt_paths: List[str], db_path: str = "data/literature.db"
) -> Tuple[LiteratureDatabaseManager, Dict[str, Any]]:
    """
    创建文献数据库的便捷函数（从WOS TXT文件列表）

    Args:
        txt_paths: WOS导出的Plain Text .txt文件路径列表
        db_path: 数据库路径

    Returns:
        (文献数据库管理器实例, 导入统计信息)
    """
    manager = LiteratureDatabaseManager(db_path)
    total_count = 0
    all_errors = []

    for txt_path in txt_paths:
        count, errors = manager.import_from_wos_txt(txt_path)
        total_count += count
        all_errors.extend(errors)

    stats = manager.get_statistics()
    stats["imported_count"] = total_count
    stats["errors"] = all_errors

    return manager, stats
