"""
向量搜索模块 - 使用sentence-transformers生成embedding进行语义搜索
"""

import numpy as np
from typing import List, Tuple, Optional
import pickle
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer

    EMBEDDING_AVAILABLE = True
except ImportError:
    EMBEDDING_AVAILABLE = False


class VectorSearchIndex:
    """向量搜索索引"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        初始化向量索引

        Args:
            model_name: sentence-transformers模型名
        """
        if not EMBEDDING_AVAILABLE:
            raise ImportError("请先安装: pip install sentence-transformers")

        self.model = SentenceTransformer(model_name)
        self.embeddings: Optional[np.ndarray] = None
        self.paper_ids: List[int] = []
        self.texts: List[str] = []

    def build_index(self, papers: List) -> None:
        """
        构建向量索引

        Args:
            papers: Paper对象列表
        """
        self.paper_ids = []
        self.texts = []

        for paper in papers:
            # 组合标题、摘要、关键词
            text = f"{paper.title} {paper.abstract} {paper.keywords}"
            self.texts.append(text)
            self.paper_ids.append(paper.id)

        # 生成embeddings
        print(f"正在生成 {len(self.texts)} 篇文献的向量嵌入...")
        self.embeddings = self.model.encode(self.texts, show_progress_bar=True)
        print("向量索引构建完成！")

    def search(self, query: str, top_k: int = 20) -> List[Tuple[int, float]]:
        """
        语义搜索

        Args:
            query: 查询文本
            top_k: 返回结果数

        Returns:
            [(paper_id, similarity_score), ...]
        """
        if self.embeddings is None:
            return []

        # 生成查询向量
        query_embedding = self.model.encode([query])

        # 计算余弦相似度
        similarities = np.dot(self.embeddings, query_embedding.T).flatten()

        # 获取top-k
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            results.append((self.paper_ids[idx], float(similarities[idx])))

        return results

    def save(self, filepath: str) -> None:
        """保存索引到文件"""
        data = {
            "embeddings": self.embeddings,
            "paper_ids": self.paper_ids,
            "texts": self.texts,
        }
        with open(filepath, "wb") as f:
            pickle.dump(data, f)

    def load(self, filepath: str) -> None:
        """从文件加载索引"""
        with open(filepath, "rb") as f:
            data = pickle.load(f)
        self.embeddings = data["embeddings"]
        self.paper_ids = data["paper_ids"]
        self.texts = data["texts"]


class HybridSearcher:
    """混合搜索器：关键词 + 向量 + 传统匹配"""

    def __init__(self, db_manager, use_vector: bool = True):
        self.db_manager = db_manager
        self.use_vector = use_vector
        self.vector_index: Optional[VectorSearchIndex] = None

        if use_vector and EMBEDDING_AVAILABLE:
            self.vector_index = VectorSearchIndex()

    def build_vector_index(self) -> None:
        """构建向量索引"""
        if not self.vector_index:
            print("向量搜索不可用，跳过索引构建")
            return

        papers = self.db_manager.get_all_papers(limit=10000)
        self.vector_index.build_index(papers)

        # 保存索引
        index_path = Path(self.db_manager.db_path).parent / "vector_index.pkl"
        self.vector_index.save(str(index_path))
        print(f"向量索引已保存至: {index_path}")

    def search(
        self,
        query: str,
        keywords: List[str],
        year_min: Optional[int] = None,
        top_k: int = 50,
    ) -> List[Tuple]:
        """
        混合搜索

        策略：
        1. 向量搜索召回候选（语义相关）
        2. 关键词搜索补充（字面匹配）
        3. 合并去重，按综合分数排序
        """
        results = []
        seen_ids = set()

        # 1. 向量搜索（如果可用）
        if self.vector_index and self.vector_index.embeddings is not None:
            vector_results = self.vector_index.search(query, top_k=top_k // 2)
            for paper_id, score in vector_results:
                if paper_id not in seen_ids:
                    seen_ids.add(paper_id)
                    results.append((paper_id, "vector", score))

        # 2. 关键词搜索
        keyword_results = self.db_manager.search_by_keywords(
            keywords=keywords, limit=top_k // 2, year_min=year_min
        )
        for paper, score in keyword_results:
            if paper.id not in seen_ids:
                seen_ids.add(paper.id)
                results.append((paper.id, "keyword", score))

        # 3. 获取完整Paper对象
        final_results = []
        for paper_id, source, score in results:
            papers = self.db_manager.search(query="", limit=1)
            # 这里需要优化，应该直接通过ID查询
            # 暂时用search占位

        return results
