"""
混合检索引擎使用示例

这是方案4完整实现的演示，展示如何使用新的 HybridSearchEngine 替代原有检索方式。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.literature.db_manager import LiteratureDatabaseManager
from src.citation.search_engine import HybridSearchEngine


def demo_basic_search():
    """基本检索示例"""
    print("=" * 60)
    print("混合检索引擎 - 基本使用示例")
    print("=" * 60)

    # 1. 初始化数据库
    db_manager = LiteratureDatabaseManager("data/literature.db")

    # 2. 初始化搜索引擎
    engine = HybridSearchEngine(
        db_manager=db_manager,
        api_manager=None,  # 如果有API管理器可以传入，用于查询扩展
        use_query_expansion=True,  # 启用查询扩展
        use_cross_encoder=True,  # 启用 Cross-encoder 重排序
        use_mmr=True,  # 启用 MMR 多样性
        mmr_lambda=0.6,  # MMR 参数：0.0纯多样，1.0纯相关
        vector_weight=0.4,  # 向量检索权重
        keyword_weight=0.3,  # 关键词检索权重
        citation_weight=0.3,  # 引用图检索权重
    )

    # 3. 构建向量索引（首次运行或数据更新后）
    print("\n构建向量索引...")
    success = engine.build_index()
    if success:
        print("✓ 向量索引构建成功")
    else:
        print("⚠ 向量索引构建失败，将使用关键词检索")

    # 4. 执行检索
    query = "effects of climate change on soil carbon"
    print(f"\n查询: {query}")
    print("-" * 60)

    results = engine.search(
        query=query,
        top_k=5,
        year_min=2020,  # 只搜索2020年后的文献
        expand_query=True,  # 扩展查询
        diversify=True,  # 应用多样性算法
    )

    # 5. 显示结果
    print(f"\n找到 {len(results)} 篇相关文献:\n")

    for i, result in enumerate(results, 1):
        paper = result.paper
        print(f"[{i}] {paper.title}")
        print(f"    作者: {paper.authors[:80]}...")
        print(f"    期刊: {paper.journal} | 年份: {paper.year}")
        print(f"    综合分数: {result.final_score:.3f}")
        print(f"    Cross-encoder: {result.cross_encoder_score:.3f}")
        print(f"    来源: {result.source}")
        if result.diversity_score > 0:
            print(f"    多样性惩罚: {result.diversity_score:.3f}")
        print()


def demo_sentence_search():
    """为句子检索引用的示例"""
    print("=" * 60)
    print("为句子检索引用")
    print("=" * 60)

    from src.draft.analyzer import Sentence

    # 初始化
    db_manager = LiteratureDatabaseManager("data/literature.db")
    engine = HybridSearchEngine(db_manager)
    engine.build_index()

    # 创建一个示例句子
    sentence = Sentence(
        text="The application of machine learning in climate prediction has shown promising results.",
        keywords=["machine learning", "climate prediction", "artificial intelligence"],
        paragraph_index=0,
    )

    print(f"\n句子: {sentence.text}")
    print(f"关键词: {', '.join(sentence.keywords)}")
    print("-" * 60)

    # 检索相关文献
    results = engine.search_for_sentence(
        sentence=sentence,
        top_k=3,
        year_range=10,  # 最近10年
    )

    print(f"\n推荐引用:\n")
    for i, result in enumerate(results, 1):
        paper = result.paper
        print(f"[{i}] {paper.title}")
        print(f"    作者: {paper.authors}")
        print(f"    相关性: {result.final_score:.3f}")
        print()


def demo_comparison():
    """对比不同配置的效果"""
    print("=" * 60)
    print("不同检索配置对比")
    print("=" * 60)

    db_manager = LiteratureDatabaseManager("data/literature.db")
    query = "nitrous oxide emission from agricultural soil"

    configs = [
        ("仅关键词", False, False, False),
        ("+ 查询扩展", True, False, False),
        ("+ Cross-encoder", True, True, False),
        ("+ MMR多样性", True, True, True),
    ]

    for name, expand, cross_encoder, mmr in configs:
        print(f"\n【{name}】")

        engine = HybridSearchEngine(
            db_manager=db_manager,
            use_query_expansion=expand,
            use_cross_encoder=cross_encoder,
            use_mmr=mmr,
        )
        engine.build_index()

        results = engine.search(query, top_k=3, expand_query=expand, diversify=mmr)

        for i, r in enumerate(results, 1):
            print(f"  {i}. {r.paper.title[:60]}... (score: {r.final_score:.3f})")


def demo_performance_test():
    """性能测试"""
    print("=" * 60)
    print("检索性能测试")
    print("=" * 60)

    import time

    db_manager = LiteratureDatabaseManager("data/literature.db")
    engine = HybridSearchEngine(db_manager)
    engine.build_index()

    queries = [
        "climate change impact",
        "machine learning algorithms",
        "soil carbon sequestration",
        "nitrogen fertilizer effects",
        "greenhouse gas emissions",
    ]

    times = []
    for query in queries:
        start = time.time()
        results = engine.search(query, top_k=10)
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"  '{query[:30]}...' : {elapsed:.3f}s")

    print(f"\n平均耗时: {sum(times) / len(times):.3f}s")
    print(f"总耗时: {sum(times):.3f}s")


if __name__ == "__main__":
    # 运行示例
    try:
        demo_basic_search()
    except Exception as e:
        print(f"基本检索示例出错: {e}")

    print("\n" + "=" * 60 + "\n")

    try:
        demo_sentence_search()
    except Exception as e:
        print(f"句子检索示例出错: {e}")

    print("\n" + "=" * 60 + "\n")

    try:
        demo_comparison()
    except Exception as e:
        print(f"对比示例出错: {e}")

    print("\n" + "=" * 60 + "\n")

    try:
        demo_performance_test()
    except Exception as e:
        print(f"性能测试出错: {e}")
