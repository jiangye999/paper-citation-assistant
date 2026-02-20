"""
混合检索引擎 - 方案4完整实现
包含：查询扩展、多路召回、Cross-encoder重排序、MMR多样性算法
"""

import os
import json
import numpy as np
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from functools import lru_cache
import hashlib
import time
from pathlib import Path

from ..literature.db_manager import LiteratureDatabaseManager, Paper
from ..draft.analyzer import Sentence


@dataclass
class SearchResult:
    """检索结果"""

    paper: Paper
    score: float
    source: str  # 'vector', 'keyword', 'citation_graph'
    original_rank: int = 0


@dataclass
class RerankedResult:
    """重排序后的结果"""

    paper: Paper
    final_score: float
    cross_encoder_score: float
    original_score: float
    source: str
    diversity_score: float = 0.0


class QueryExpander:
    """查询扩展器 - 使用LLM生成同义查询"""

    def __init__(self, api_manager=None):
        self.api_manager = api_manager
        self._cache: Dict[str, List[str]] = {}

    def expand(self, query: str, max_expansions: int = 3) -> List[str]:
        """
        扩展查询，生成同义改写

        Args:
            query: 原始查询
            max_expansions: 最大扩展数量

        Returns:
            扩展后的查询列表（包含原始查询）
        """
        # 检查缓存
        cache_key = hashlib.md5(query.encode()).hexdigest()
        if cache_key in self._cache:
            return [query] + self._cache[cache_key][:max_expansions]

        if not self.api_manager:
            # 无API时使用简单的同义词替换
            return self._simple_expand(query, max_expansions)

        try:
            expanded = self._llm_expand(query, max_expansions)
            self._cache[cache_key] = expanded
            return [query] + expanded
        except Exception as e:
            print(f"查询扩展失败: {e}")
            return [query]

    def _llm_expand(self, query: str, max_expansions: int) -> List[str]:
        """使用LLM进行查询扩展"""
        prompt = f"""Generate {max_expansions} alternative search queries that capture the same meaning as the original query. These queries will be used to search for academic papers.

Original query: "{query}"

Provide alternative queries that:
1. Use synonyms or related terms
2. Change sentence structure but keep meaning
3. Include more general or specific terms where appropriate

Return ONLY a JSON array of strings, no other text:
["alternative query 1", "alternative query 2", "alternative query 3"]"""

        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant for academic search query expansion. Respond only in JSON format.",
            },
            {"role": "user", "content": prompt},
        ]

        response = self.api_manager.call_model(
            messages, temperature=0.7, max_tokens=500
        )

        # 解析JSON
        import re

        json_match = re.search(r"\[.*?\]", response, re.DOTALL)
        if json_match:
            try:
                expansions = json.loads(json_match.group())
                return [e for e in expansions if isinstance(e, str)][:max_expansions]
            except json.JSONDecodeError:
                pass

        return []

    def _simple_expand(self, query: str, max_expansions: int) -> List[str]:
        """简单的查询扩展（无API时的降级方案）"""
        # 学术领域常见同义词
        synonyms = {
            "effect": ["impact", "influence", "role"],
            "increase": ["rise", "growth", "enhancement"],
            "decrease": ["reduction", "decline", "drop"],
            "improve": ["enhance", "boost", "optimize"],
            "analyze": ["examine", "investigate", "study"],
            "method": ["approach", "technique", "strategy"],
            "result": ["outcome", "finding", "conclusion"],
            "significant": ["substantial", "considerable", "marked"],
        }

        expansions = []
        words = query.lower().split()

        for word in words:
            if word in synonyms and len(expansions) < max_expansions:
                for syn in synonyms[word][:1]:  # 每个词只用一个同义词
                    new_query = query.replace(word, syn, 1)
                    if new_query not in expansions and new_query != query:
                        expansions.append(new_query)
                        break

        return [query] + expansions


class VectorRetriever:
    """向量检索器 - 使用 FAISS 加速"""

    def __init__(self, db_manager: LiteratureDatabaseManager):
        self.db_manager = db_manager
        self.embeddings: Optional[np.ndarray] = None
        self.paper_ids: List[int] = []
        self.texts: List[str] = []
        self._faiss_index = None
        self._index_built = False

        # 尝试导入 FAISS
        try:
            import faiss

            self.faiss = faiss
            self.FAISS_AVAILABLE = True
        except ImportError:
            self.FAISS_AVAILABLE = False
            print("警告: FAISS 未安装，将使用原生向量检索。安装: pip install faiss-cpu")

        # 尝试导入 sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer

            # 设置 HuggingFace 镜像源（国内访问）
            import os

            if not os.environ.get("HF_ENDPOINT"):
                os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

            # 使用离线模式如果模型已下载
            local_model_path = self._get_local_model_path()
            if local_model_path:
                self.model = SentenceTransformer(local_model_path)
            else:
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
            self.EMBEDDING_AVAILABLE = True
        except ImportError:
            self.EMBEDDING_AVAILABLE = False
            print("警告: sentence-transformers 未安装")
        except Exception as e:
            print(f"警告: 模型加载失败 - {e}")
            print("提示: 设置 HF_ENDPOINT=https://hf-mirror.com 或使用离线模式")
            self.EMBEDDING_AVAILABLE = False

    def _get_local_model_path(self) -> str:
        """查找本地缓存的模型路径，如果不存在则自动下载"""
        from pathlib import Path

        # 优先检查项目目录下的 models 文件夹
        project_model_path = (
            Path(__file__).parent.parent.parent / "models" / "all-MiniLM-L6-v2"
        )
        if project_model_path.exists() and any(project_model_path.iterdir()):
            return str(project_model_path)

        # 检查exe同目录下的models文件夹
        exe_dir = (
            Path(sys.executable).parent if getattr(sys, "frozen", False) else Path.cwd()
        )
        exe_model_path = exe_dir / "models" / "all-MiniLM-L6-v2"
        if exe_model_path.exists() and any(exe_model_path.iterdir()):
            return str(exe_model_path)

        # 常见缓存路径
        cache_paths = [
            Path.home() / ".cache" / "torch" / "sentence_transformers",
            Path.home() / ".cache" / "huggingface" / "hub",
        ]

        model_name = "sentence-transformers_all-MiniLM-L6-v2"

        for cache_path in cache_paths:
            if cache_path.exists():
                for item in cache_path.iterdir():
                    if model_name in str(item):
                        return str(item)

        # 如果模型不存在，尝试自动下载
        print("正在检查模型...")
        try:
            from sentence_transformers import SentenceTransformer
            import os

            if not os.environ.get("HF_ENDPOINT"):
                os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

            # 创建models目录
            download_path = project_model_path.parent
            download_path.mkdir(parents=True, exist_ok=True)

            print(f"首次运行，正在下载AI模型（约100MB）...")
            print("请稍候...")

            # 下载模型
            model = SentenceTransformer(
                "sentence-transformers/all-MiniLM-L6-v2",
                cache_folder=str(download_path.parent),
            )

            # 返回新下载的模型路径
            new_path = download_path / "sentence-transformers_all-MiniLM-L6-v2"
            if new_path.exists():
                # 重命名
                import shutil

                shutil.move(str(new_path), str(project_model_path))
                return str(project_model_path)

        except Exception as e:
            print(f"自动下载模型失败: {e}")

        return ""

    def build_index(self, force_rebuild: bool = False) -> bool:
        """构建向量索引"""
        if not self.EMBEDDING_AVAILABLE:
            return False

        index_path = Path(self.db_manager.db_path).parent / "faiss_index.bin"
        metadata_path = Path(self.db_manager.db_path).parent / "faiss_metadata.json"

        # 尝试加载已有索引
        if not force_rebuild and index_path.exists() and metadata_path.exists():
            try:
                return self._load_index(str(index_path), str(metadata_path))
            except Exception as e:
                print(f"加载索引失败，重新构建: {e}")

        # 获取所有文献
        papers = self.db_manager.get_all_papers(limit=10000)
        if not papers:
            print("数据库为空")
            return False

        print(f"正在为 {len(papers)} 篇文献构建向量索引...")

        self.paper_ids = []
        self.texts = []

        for paper in papers:
            # 组合文本（标题权重最高）
            text = f"{paper.title}. {paper.title}. {paper.abstract} {paper.keywords}"
            self.texts.append(text)
            self.paper_ids.append(paper.id)

        # 生成 embeddings
        print("生成向量嵌入...")
        self.embeddings = self.model.encode(
            self.texts, show_progress_bar=True, batch_size=32
        )

        # 归一化（用于余弦相似度）
        self.embeddings = self.embeddings / np.linalg.norm(
            self.embeddings, axis=1, keepdims=True
        )

        # 构建 FAISS 索引
        if self.FAISS_AVAILABLE:
            dimension = self.embeddings.shape[1]
            self._faiss_index = self.faiss.IndexFlatIP(
                dimension
            )  # 内积 = 余弦相似度（归一化后）
            self._faiss_index.add(self.embeddings.astype("float32"))

            # 保存索引
            self.faiss.write_index(self._faiss_index, str(index_path))

        # 保存元数据
        metadata = {
            "paper_ids": self.paper_ids,
            "texts": self.texts,
            "embedding_dim": self.embeddings.shape[1],
            "paper_count": len(papers),
        }
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False)

        self._index_built = True
        print("向量索引构建完成！")
        return True

    def _load_index(self, index_path: str, metadata_path: str) -> bool:
        """加载已有索引"""
        if not self.FAISS_AVAILABLE:
            return False

        self._faiss_index = self.faiss.read_index(index_path)

        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            self.paper_ids = metadata["paper_ids"]
            self.texts = metadata["texts"]

        self._index_built = True
        print(f"加载已有向量索引: {len(self.paper_ids)} 篇文献")
        return True

    @lru_cache(maxsize=100)
    def _get_query_embedding(self, query: str) -> np.ndarray:
        """缓存查询向量"""
        if not self.EMBEDDING_AVAILABLE:
            return np.array([])
        embedding = self.model.encode([query])
        return embedding / np.linalg.norm(embedding, axis=1, keepdims=True)

    def search(self, query: str, top_k: int = 50) -> List[Tuple[int, float]]:
        """
        向量检索

        Returns:
            [(paper_id, score), ...]
        """
        if not self._index_built or not self.EMBEDDING_AVAILABLE:
            return []

        query_embedding = self._get_query_embedding(query)

        if self.FAISS_AVAILABLE and self._faiss_index is not None:
            # FAISS 搜索
            scores, indices = self._faiss_index.search(
                query_embedding.astype("float32"), top_k
            )
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0 and idx < len(self.paper_ids):
                    results.append((self.paper_ids[idx], float(score)))
            return results
        else:
            # 原生 numpy 搜索（降级方案）
            if self.embeddings is None:
                return []
            similarities = np.dot(self.embeddings, query_embedding.T).flatten()
            top_indices = np.argsort(similarities)[::-1][:top_k]
            return [
                (self.paper_ids[idx], float(similarities[idx])) for idx in top_indices
            ]


class CrossEncoderReranker:
    """Cross-encoder 重排序器"""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self.model = None
        self._initialized = False

        try:
            from sentence_transformers import CrossEncoder

            self.CrossEncoder = CrossEncoder
            self.AVAILABLE = True
        except ImportError:
            self.AVAILABLE = False

    def _init_model(self):
        """延迟加载模型"""
        if not self._initialized and self.AVAILABLE:
            print(f"加载 Cross-encoder 模型: {self.model_name}")

            # 优先从本地 models 目录加载
            local_model_path = self._get_local_model_path()
            if local_model_path:
                print(f"  从本地加载: {local_model_path}")
                self.model = self.CrossEncoder(local_model_path)
            else:
                self.model = self.CrossEncoder(self.model_name)
            self._initialized = True

    def _get_local_model_path(self) -> str:
        """查找本地缓存的模型路径"""
        from pathlib import Path

        # 优先检查项目目录下的 models 文件夹
        project_model_path = (
            Path(__file__).parent.parent.parent
            / "models"
            / self.model_name.replace("/", "_")
        )
        if project_model_path.exists():
            return str(project_model_path)

        # 检查 HuggingFace 缓存路径
        cache_paths = [
            Path.home() / ".cache" / "torch" / "sentence_transformers",
            Path.home() / ".cache" / "huggingface" / "hub",
        ]

        model_name = self.model_name.replace("/", "_")

        for cache_path in cache_paths:
            if cache_path.exists():
                for item in cache_path.iterdir():
                    if model_name in str(item) and item.is_dir():
                        return str(item)

        return ""

    def rerank(
        self, query: str, candidates: List[SearchResult], top_k: int = 20
    ) -> List[RerankedResult]:
        """
        重排序候选结果

        Args:
            query: 查询语句
            candidates: 候选结果列表
            top_k: 返回数量

        Returns:
            重排序后的结果
        """
        if not candidates:
            return []

        # 如果 cross-encoder 不可用，直接返回按原分数排序的结果
        if not self.AVAILABLE:
            return [
                RerankedResult(
                    paper=c.paper,
                    final_score=c.score,
                    cross_encoder_score=c.score,
                    original_score=c.score,
                    source=c.source,
                )
                for c in sorted(candidates, key=lambda x: x.score, reverse=True)[:top_k]
            ]

        self._init_model()

        # 准备输入
        pairs = []
        for c in candidates:
            paper_text = f"{c.paper.title}. {c.paper.abstract[:300]}"
            pairs.append([query, paper_text])

        # 预测相关性分数
        scores = self.model.predict(pairs, show_progress_bar=False)

        # 组合结果
        reranked = []
        for i, (candidate, ce_score) in enumerate(zip(candidates, scores)):
            # 综合分数：cross-encoder 权重 70%，原始分数 30%
            combined_score = ce_score * 0.7 + candidate.score * 0.3

            reranked.append(
                RerankedResult(
                    paper=candidate.paper,
                    final_score=combined_score,
                    cross_encoder_score=float(ce_score),
                    original_score=candidate.score,
                    source=candidate.source,
                )
            )

        # 按综合分数排序
        reranked.sort(key=lambda x: x.final_score, reverse=True)
        return reranked[:top_k]


class MMRDiversifier:
    """MMR (Maximal Marginal Relevance) 多样性算法"""

    def __init__(self, lambda_param: float = 0.5):
        """
        Args:
            lambda_param: 相关性 vs 多样性的权衡参数
                         0.0 = 完全多样性，1.0 = 完全相关性
        """
        self.lambda_param = lambda_param

    def diversify(
        self, query: str, results: List[RerankedResult], top_k: int = 10
    ) -> List[RerankedResult]:
        """
        使用 MMR 算法选择多样化的结果

        Args:
            query: 查询语句
            results: 已重排序的结果（包含分数）
            top_k: 最终返回数量

        Returns:
            多样化后的结果
        """
        if not results or top_k <= 0:
            return []

        if len(results) <= top_k:
            return results

        # 提取文本用于计算相似度
        texts = []
        for r in results:
            text = f"{r.paper.title}. {r.paper.abstract[:200]}"
            texts.append(text)

        # 计算文本之间的相似度矩阵
        selected = []
        remaining = list(range(len(results)))

        # 第一个选择：相关性最高的
        first_idx = max(remaining, key=lambda i: results[i].final_score)
        selected.append(first_idx)
        remaining.remove(first_idx)

        # MMR 选择
        while len(selected) < top_k and remaining:
            mmr_scores = []

            for idx in remaining:
                relevance = results[idx].final_score

                # 计算与已选结果的最大相似度
                max_sim = 0.0
                for sel_idx in selected:
                    sim = self._text_similarity(texts[idx], texts[sel_idx])
                    max_sim = max(max_sim, sim)

                # MMR 分数
                mmr_score = (
                    self.lambda_param * relevance - (1 - self.lambda_param) * max_sim
                )
                mmr_scores.append((idx, mmr_score, max_sim))

            # 选择 MMR 分数最高的
            best_idx, _, diversity_penalty = max(mmr_scores, key=lambda x: x[1])
            results[best_idx].diversity_score = diversity_penalty
            selected.append(best_idx)
            remaining.remove(best_idx)

        return [results[i] for i in selected]

    def _text_similarity(self, text1: str, text2: str) -> float:
        """计算两段文本的相似度（简单 Jaccard）"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0


class HybridSearchEngine:
    """
    混合搜索引擎 - 整合所有检索组件

    流程：
    1. 查询扩展 -> 2. 多路召回 -> 3. Cross-encoder重排序 -> 4. MMR多样性
    """

    def __init__(
        self,
        db_manager: LiteratureDatabaseManager,
        api_manager=None,
        use_query_expansion: bool = True,
        use_cross_encoder: bool = True,
        use_mmr: bool = True,
        mmr_lambda: float = 0.6,
        vector_weight: float = 0.4,
        keyword_weight: float = 0.3,
        citation_weight: float = 0.3,
    ):
        """
        初始化混合搜索引擎

        Args:
            db_manager: 文献数据库管理器
            api_manager: AI API 管理器（用于查询扩展）
            use_query_expansion: 是否使用查询扩展
            use_cross_encoder: 是否使用 Cross-encoder 重排序
            use_mmr: 是否使用 MMR 多样性算法
            mmr_lambda: MMR 权衡参数
            vector_weight: 向量检索权重
            keyword_weight: 关键词检索权重
            citation_weight: 引用图检索权重
        """
        self.db_manager = db_manager
        self.api_manager = api_manager

        # 初始化各组件
        self.query_expander = (
            QueryExpander(api_manager) if use_query_expansion else None
        )
        self.vector_retriever = VectorRetriever(db_manager)
        self.cross_encoder = CrossEncoderReranker() if use_cross_encoder else None
        self.mmr = MMRDiversifier(mmr_lambda) if use_mmr else None

        # 权重配置
        self.weights = {
            "vector": vector_weight,
            "keyword": keyword_weight,
            "citation": citation_weight,
        }

        self._vector_index_built = False

    def build_index(self) -> bool:
        """构建向量索引"""
        self._vector_index_built = self.vector_retriever.build_index()
        return self._vector_index_built

    def search(
        self,
        query: str,
        top_k: int = 10,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        expand_query: bool = True,
        diversify: bool = True,
    ) -> List[RerankedResult]:
        """
        执行混合检索

        Args:
            query: 查询语句
            top_k: 返回结果数
            year_min: 最早年份
            year_max: 最晚年份
            expand_query: 是否进行查询扩展
            diversify: 是否应用 MMR 多样性

        Returns:
            最终检索结果
        """
        start_time = time.time()

        # 1. 查询扩展
        queries = [query]
        if expand_query and self.query_expander:
            queries = self.query_expander.expand(query, max_expansions=2)
            print(f"查询扩展: {len(queries)} 个查询 - {queries}")

        # 2. 多路召回
        candidates = self._multi_retrieve(
            queries,
            top_k=top_k * 5,  # 召回更多用于后续筛选
            year_min=year_min,
            year_max=year_max,
        )

        if not candidates:
            return []

        print(f"多路召回: {len(candidates)} 篇候选文献")

        # 3. Cross-encoder 重排序
        if self.cross_encoder:
            reranked = self.cross_encoder.rerank(query, candidates, top_k=top_k * 2)
        else:
            reranked = [
                RerankedResult(
                    paper=c.paper,
                    final_score=c.score,
                    cross_encoder_score=c.score,
                    original_score=c.score,
                    source=c.source,
                )
                for c in sorted(candidates, key=lambda x: x.score, reverse=True)[
                    : top_k * 2
                ]
            ]

        # 4. MMR 多样性
        if diversify and self.mmr:
            final_results = self.mmr.diversify(query, reranked, top_k=top_k)
        else:
            final_results = reranked[:top_k]

        elapsed = time.time() - start_time
        print(f"检索完成: {len(final_results)} 篇，耗时 {elapsed:.2f}s")

        return final_results

    def _multi_retrieve(
        self,
        queries: List[str],
        top_k: int,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
    ) -> List[SearchResult]:
        """
        多路召回：向量检索 + 关键词检索 + 引用图

        Args:
            queries: 查询列表（可能包含扩展查询）
            top_k: 召回数量
            year_min: 最早年份
            year_max: 最晚年份

        Returns:
            合并后的候选结果
        """
        # 收集所有候选
        candidate_map: Dict[int, SearchResult] = {}

        # 1. 向量检索
        if self._vector_index_built:
            for query in queries:
                vector_results = self.vector_retriever.search(
                    query, top_k=max(10, int(top_k * self.weights["vector"]))
                )

                for paper_id, score in vector_results:
                    if paper_id not in candidate_map:
                        # 获取完整 Paper 对象
                        papers = self.db_manager.search(query="", limit=1)
                        if papers:
                            paper = papers[0]
                            candidate_map[paper_id] = SearchResult(
                                paper=paper,
                                score=score * self.weights["vector"],
                                source="vector",
                            )
                    else:
                        # 合并分数
                        candidate_map[paper_id].score = max(
                            candidate_map[paper_id].score,
                            score * self.weights["vector"],
                        )

        # 2. 关键词检索
        for query in queries:
            keywords = self._extract_keywords(query)
            if keywords:
                keyword_results = self.db_manager.search_by_keywords(
                    keywords=keywords,
                    limit=max(10, int(top_k * self.weights["keyword"])),
                    year_min=year_min,
                    year_max=year_max,
                )

                for paper, score in keyword_results:
                    if paper.id not in candidate_map:
                        candidate_map[paper.id] = SearchResult(
                            paper=paper,
                            score=score * self.weights["keyword"],
                            source="keyword",
                        )
                    else:
                        # 合并分数（取最大）
                        candidate_map[paper.id].score = max(
                            candidate_map[paper.id].score,
                            score * self.weights["keyword"],
                        )

        # 3. 引用图检索（基于高引用论文的共引）
        # 简化的实现：查找高引用论文
        citation_results = self.db_manager.search(
            query=queries[0],
            limit=max(5, int(top_k * self.weights["citation"])),
            cited_by_min=50,
            year_min=year_min,
            year_max=year_max,
        )

        for paper in citation_results:
            if paper.id not in candidate_map:
                # 高引用论文给予基础分数
                base_score = min(0.5, paper.cited_by / 500) * self.weights["citation"]
                candidate_map[paper.id] = SearchResult(
                    paper=paper, score=base_score, source="citation"
                )

        # 过滤年份
        filtered = []
        for result in candidate_map.values():
            if year_min and result.paper.year < year_min:
                continue
            if year_max and result.paper.year > year_max:
                continue
            filtered.append(result)

        # 按分数排序
        filtered.sort(key=lambda x: x.score, reverse=True)
        return filtered[:top_k]

    def _extract_keywords(self, text: str) -> List[str]:
        """从文本中提取关键词"""
        # 简单的关键词提取：移除停用词，保留名词性词汇
        import re

        # 停用词
        stopwords = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "this",
            "that",
            "these",
            "those",
            "study",
            "research",
            "analysis",
            "using",
            "based",
            "show",
            "showed",
            "shown",
            "found",
            "results",
        }

        # 提取单词（长度>3）
        words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
        keywords = [w for w in words if w not in stopwords]

        # 去重并限制数量
        return list(dict.fromkeys(keywords))[:10]

    def search_for_sentence(
        self,
        sentence: Sentence,
        top_k: int = 3,
        year_range: int = 10,
    ) -> List[RerankedResult]:
        """
        为单个句子检索相关文献（便捷方法）

        Args:
            sentence: Sentence 对象
            top_k: 返回数量
            year_range: 年份范围（当前年份往前）

        Returns:
            检索结果
        """
        import datetime

        current_year = datetime.datetime.now().year
        year_min = current_year - year_range

        # 使用句子文本和关键词构建查询
        query = sentence.text
        if sentence.keywords:
            query += " " + " ".join(sentence.keywords[:5])

        return self.search(
            query=query,
            top_k=top_k,
            year_min=year_min,
            expand_query=True,
            diversify=True,
        )
