"""
快速测试脚本 - 验证混合检索引擎集成
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("混合检索引擎集成测试")
print("=" * 60)

# 1. 测试导入
try:
    from src.citation.search_engine import HybridSearchEngine, QueryExpander
    from src.citation.ai_matcher import AICitationMatcher, AIAPIManager

    print("✅ 模块导入成功")
except Exception as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

# 2. 测试数据库连接
try:
    from src.literature.db_manager import LiteratureDatabaseManager

    db_manager = LiteratureDatabaseManager("data/literature.db")
    stats = db_manager.get_statistics()
    print(f"✅ 数据库连接成功")
    print(f"   文献数量: {stats['total_papers']} 篇")
except Exception as e:
    print(f"⚠️ 数据库连接警告: {e}")
    print("   这是正常的，如果没有导入过文献")

# 3. 测试 AICitationMatcher 初始化
try:
    # 模拟 API 管理器
    class MockAPIManager:
        def call_model(self, messages, temperature=0.3, max_tokens=2000):
            return '{"evaluations": []}'

    api_manager = MockAPIManager()

    # 测试禁用混合检索
    matcher_traditional = AICitationMatcher(
        db_manager=db_manager, api_manager=api_manager, use_hybrid_search=False
    )
    print("✅ 传统模式 AICitationMatcher 初始化成功")

    # 测试启用混合检索
    matcher_hybrid = AICitationMatcher(
        db_manager=db_manager, api_manager=api_manager, use_hybrid_search=True
    )
    print("✅ 混合检索模式 AICitationMatcher 初始化成功")

    if matcher_hybrid.use_hybrid_search and matcher_hybrid.search_engine is not None:
        print("✅ 混合检索引擎已正确加载")
    else:
        print("⚠️ 混合检索引擎未加载（可能依赖未安装）")

except Exception as e:
    print(f"⚠️ AICitationMatcher 初始化警告: {e}")
    print("   这可能是由于依赖未安装造成的")

# 4. 测试 HybridSearchEngine 独立使用
try:
    engine = HybridSearchEngine(
        db_manager=db_manager,
        api_manager=None,  # 可以不传API管理器
        use_query_expansion=False,  # 无API时不使用查询扩展
        use_cross_encoder=True,
        use_mmr=True,
    )
    print("✅ HybridSearchEngine 独立初始化成功")
except Exception as e:
    print(f"⚠️ HybridSearchEngine 初始化警告: {e}")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)
print("\n下一步操作:")
print("1. 如果文献库有数据，首次使用时会自动构建向量索引")
print("2. 运行: streamlit run app.py")
print("3. 在侧边栏可以看到'启用混合检索引擎'选项")
