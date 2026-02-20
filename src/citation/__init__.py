"""
Citation module - 引用匹配与检索模块

包含以下子模块:
- matcher: 基础TF-IDF匹配
- ai_matcher: AI辅助匹配
- search_engine: 混合检索引擎（方案4完整实现）
- rag_retriever: RAG向量检索
- vector_search: 原向量搜索
- format_learner: 参考文献格式学习
"""

from .matcher import CitationMatcher, CitationMatch, SentenceWithCitations
from .search_engine import (
    HybridSearchEngine,
    QueryExpander,
    VectorRetriever,
    CrossEncoderReranker,
    MMRDiversifier,
    SearchResult,
    RerankedResult,
)

__all__ = [
    # 基础匹配
    "CitationMatcher",
    "CitationMatch",
    "SentenceWithCitations",
    # 混合检索引擎
    "HybridSearchEngine",
    "QueryExpander",
    "VectorRetriever",
    "CrossEncoderReranker",
    "MMRDiversifier",
    "SearchResult",
    "RerankedResult",
]
