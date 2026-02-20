"""
RAG检索模块 - 使用向量数据库 + LLM进行智能检索
"""

import os
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from pathlib import Path

try:
    from llama_index.core import (
        VectorStoreIndex,
        Document,
        StorageContext,
        load_index_from_storage,
    )
    from llama_index.core.node_parser import SentenceSplitter
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding

    LLAMA_INDEX_AVAILABLE = True
except ImportError:
    LLAMA_INDEX_AVAILABLE = False

from ..literature.db_manager import LiteratureDatabaseManager, Paper


@dataclass
class RAGDocument:
    """RAG文档"""

    paper: Paper
    content: str
    metadata: Dict[str, Any]


class RAGRetriever:
    """RAG检索器"""

    def __init__(
        self,
        db_manager: LiteratureDatabaseManager,
        library_name: str = "default",
        data_dir: str = "data/libraries",
    ):
        """
        初始化RAG检索器

        Args:
            db_manager: 文献数据库管理器
            library_name: 文献库名称
            data_dir: 文献库存储目录
        """
        self.db_manager = db_manager
        self.library_name = library_name
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.index_path = self.data_dir / f"{library_name}_rag_index"
        self.metadata_path = self.data_dir / f"{library_name}_metadata.json"

        self.index = None
        self.documents: Dict[int, RAGDocument] = {}

        if LLAMA_INDEX_AVAILABLE:
            self.embed_model = HuggingFaceEmbedding(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
        else:
            self.embed_model = None

    def build_index(self, force_rebuild: bool = False) -> bool:
        """
        构建RAG索引

        Args:
            force_rebuild: 是否强制重建

        Returns:
            是否成功
        """
        if not LLAMA_INDEX_AVAILABLE:
            print("LlamaIndex不可用，请安装: pip install llama-index")
            return False

        # 检查是否已有索引
        if not force_rebuild and self.index_path.exists():
            print(f"加载已有索引: {self.index_path}")
            self._load_index()
            return True

        # 获取所有文献
        papers = self.db_manager.get_all_papers(limit=10000)
        if not papers:
            print("数据库为空，无法构建索引")
            return False

        print(f"正在为 {len(papers)} 篇文献构建RAG索引...")

        # 创建文档
        documents = []
        for paper in papers:
            # 组合文献内容
            content = f"""
Title: {paper.title}
Authors: {paper.authors}
Journal: {paper.journal}
Year: {paper.year}
Abstract: {paper.abstract}
Keywords: {paper.keywords}
Cited by: {paper.cited_by}
            """.strip()

            # 元数据
            metadata = {
                "paper_id": paper.id,
                "title": paper.title,
                "authors": paper.authors,
                "year": paper.year,
                "journal": paper.journal,
                "cited_by": paper.cited_by,
                "doi": paper.doi,
            }

            # 创建LlamaIndex文档
            doc = Document(text=content, metadata=metadata, doc_id=str(paper.id))
            documents.append(doc)

            # 缓存到内存
            self.documents[paper.id] = RAGDocument(
                paper=paper, content=content, metadata=metadata
            )

        # 构建索引
        try:
            # 使用句子分割器
            node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)

            # 构建向量索引
            self.index = VectorStoreIndex.from_documents(
                documents, embed_model=self.embed_model, node_parser=node_parser
            )

            # 保存索引
            self.index.storage_context.persist(persist_dir=str(self.index_path))

            # 保存元数据
            self._save_metadata()

            print(f"RAG索引构建完成！保存在: {self.index_path}")
            return True

        except Exception as e:
            print(f"构建索引失败: {e}")
            return False

    def _load_index(self) -> bool:
        """加载已有索引"""
        if not LLAMA_INDEX_AVAILABLE:
            return False

        try:
            storage_context = StorageContext.from_defaults(
                persist_dir=str(self.index_path)
            )
            self.index = load_index_from_storage(
                storage_context, embed_model=self.embed_model
            )
            self._load_metadata()
            return True
        except Exception as e:
            print(f"加载索引失败: {e}")
            return False

    def _save_metadata(self):
        """保存元数据"""
        metadata = {
            "library_name": self.library_name,
            "document_count": len(self.documents),
            "documents": {str(k): v.metadata for k, v in self.documents.items()},
        }
        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    def _load_metadata(self):
        """加载元数据"""
        if self.metadata_path.exists():
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 这里可以恢复documents缓存

    def retrieve(
        self, query: str, top_k: int = 20, year_range: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        检索相关文献

        Args:
            query: 查询语句
            top_k: 返回数量
            year_range: (min_year, max_year) 年份过滤

        Returns:
            检索结果列表
        """
        if not self.index:
            print("索引未构建，请先调用build_index()")
            return []

        # 创建检索器
        retriever = self.index.as_retriever(
            similarity_top_k=top_k * 2
        )  # 获取更多用于过滤

        # 检索
        nodes = retriever.retrieve(query)

        results = []
        for node in nodes:
            metadata = node.metadata
            paper_id = metadata.get("paper_id")

            # 年份过滤
            if year_range:
                year = metadata.get("year", 0)
                if year < year_range[0] or year > year_range[1]:
                    continue

            results.append(
                {
                    "paper_id": paper_id,
                    "title": metadata.get("title"),
                    "authors": metadata.get("authors"),
                    "year": metadata.get("year"),
                    "journal": metadata.get("journal"),
                    "score": node.score if hasattr(node, "score") else 0.0,
                    "content": node.text[:500],  # 前500字符
                }
            )

        return results[:top_k]

    def query_with_llm(
        self, query: str, api_manager=None, top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        使用LLM进行RAG查询（检索+重排序）

        Args:
            query: 查询语句
            api_manager: AI API管理器
            top_k: 返回数量

        Returns:
            LLM排序后的结果
        """
        # 1. 向量检索
        candidates = self.retrieve(query, top_k=top_k * 3)

        if not api_manager or not candidates:
            return candidates[:top_k]

        # 2. LLM重排序
        return self._llm_rerank(query, candidates, api_manager, top_k)

    def _llm_rerank(
        self, query: str, candidates: List[Dict], api_manager, top_k: int
    ) -> List[Dict]:
        """使用LLM重排序候选文献"""

        # 构建提示
        prompt = f"""Evaluate the relevance of each paper to the query sentence.

Query: "{query}"

Candidate Papers:
"""
        for i, cand in enumerate(candidates[:15], 1):  # 最多评估15篇
            prompt += f"""
[{i}] {cand["title"]}
    Authors: {cand["authors"]}
    Year: {cand["year"]}
    Content: {cand["content"][:300]}...
"""

        prompt += """
Rate each paper's relevance from 0.0 to 1.0 and return ONLY a JSON array:
[
  {"rank": 1, "paper_id": "...", "relevance_score": 0.95, "reason": "..."},
  {"rank": 2, "paper_id": "...", "relevance_score": 0.88, "reason": "..."}
]
"""

        messages = [
            {
                "role": "system",
                "content": "You are an expert at evaluating academic paper relevance. Respond only in JSON format.",
            },
            {"role": "user", "content": prompt},
        ]

        try:
            response = api_manager.call_model(
                messages, temperature=0.3, max_tokens=1500
            )

            # 解析JSON
            import re

            json_match = re.search(r"\[.*\]", response, re.DOTALL)
            if json_match:
                rankings = json.loads(json_match.group())

                # 重建结果列表
                paper_id_to_cand = {str(c["paper_id"]): c for c in candidates}
                reranked = []

                for rank in rankings[:top_k]:
                    paper_id = str(rank.get("paper_id"))
                    if paper_id in paper_id_to_cand:
                        cand = paper_id_to_cand[paper_id]
                        cand["llm_score"] = rank.get("relevance_score", 0)
                        cand["llm_reason"] = rank.get("reason", "")
                        reranked.append(cand)

                return reranked
        except Exception as e:
            print(f"LLM重排序失败: {e}")

        # 失败时返回原始结果
        return candidates[:top_k]

    def get_library_info(self) -> Dict[str, Any]:
        """获取文献库信息"""
        info = {
            "library_name": self.library_name,
            "index_path": str(self.index_path),
            "exists": self.index_path.exists(),
            "document_count": len(self.documents),
        }

        if self.metadata_path.exists():
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
                info.update(metadata)

        return info

    def delete_library(self) -> bool:
        """删除文献库"""
        try:
            import shutil

            if self.index_path.exists():
                shutil.rmtree(self.index_path)
            if self.metadata_path.exists():
                self.metadata_path.unlink()
            return True
        except Exception as e:
            print(f"删除文献库失败: {e}")
            return False
