# AGENTS.md - 论文反插助手开发指南

## 项目概述

基于AI的学术论文引用自动插入工具，使用 Streamlit 构建 Web 界面，支持从 Web of Science 导入文献并为草稿自动匹配引用。

## 构建/运行命令

```bash
# 安装依赖
pip install -r requirements.txt

# 运行应用
streamlit run app.py

# 应用将在 http://localhost:8501 启动
```

## 测试命令

```bash
# 运行集成测试脚本
python test_integration.py

# 单独测试某个模块
python -c "from src.literature.db_manager import LiteratureDatabaseManager; print('OK')"
python -c "from src.draft.analyzer import DraftAnalyzer; print('OK')"
python -c "from src.citation.matcher import CitationMatcher; print('OK')"
```

## 代码检查

```bash
# 安装 ruff (如未安装)
pip install ruff

# 运行 linting
ruff check .

# 自动修复
ruff check --fix .
```

## 项目结构

```
论文反插助手/
├── app.py                      # Streamlit 主入口
├── src/
│   ├── literature/
│   │   └── db_manager.py       # SQLite 文献数据库管理
│   ├── draft/
│   │   ├── analyzer.py         # Word 文档分析与句子分割
│   │   └── context_understanding.py  # 上下文理解
│   ├── citation/
│   │   ├── matcher.py          # 基础引用匹配（TF-IDF）
│   │   ├── ai_matcher.py       # AI 辅助语义匹配
│   │   ├── rag_retriever.py    # RAG 向量检索（LlamaIndex）
│   │   ├── vector_search.py    # Sentence-Transformers 向量搜索
│   │   ├── search_engine.py    # 混合搜索引擎
│   │   └── format_learner.py   # AI 学习参考文献格式
│   └── utils/
│       └── config.py           # 配置管理
├── config/config.yaml          # 用户配置文件
├── data/                       # SQLite 数据库和向量索引
├── uploads/                    # 上传文件临时存储
├── output/                     # 生成的文档输出
├── test_integration.py         # 集成测试脚本
└── requirements.txt            # 依赖清单
```

## 代码风格指南

### Python 规范

- **类型注解**：所有函数参数和返回值必须添加类型注解
- **文档字符串**：使用 Google 风格 docstring
- **导入排序**：标准库 → 第三方库 → 本地模块，每组空一行
- **行长度**：不超过 100 字符
- **命名**：
  - 类名：`PascalCase`
  - 函数/变量：`snake_case`
  - 常量：`UPPER_SNAKE_CASE`
  - 私有方法：`_leading_underscore`

### 错误处理

```python
# 必须捕获具体异常，禁止裸 except
try:
    result = risky_operation()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    return default_value
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    raise
```

### 数据库操作

- 使用上下文管理器确保连接关闭
- SQL 参数化查询，禁止字符串拼接
- 批量操作使用事务

### AI API 调用

- 所有 LLM 调用必须有超时设置（默认 30s）
- 实现指数退避重试机制（最多 3 次）
- 响应解析失败时返回优雅降级结果

## 核心模块说明

### 文献导入 (db_manager.py)

- 解析 Web of Science Plain Text 格式
- 自动生成 citekey（AuthorYear 格式）
- 支持增量导入（基于 DOI/WOS ID 去重）

### 引用匹配策略

系统采用**两步筛选法**：

1. **语义筛选**：选出最相关的前 N 篇（默认 50）
2. **加权排序**：在 N 篇中按新颖度和引用次数排序

权重配置通过 UI 调节，存储在 session state。

### 向量检索实现

- **RAGRetriever**：基于 LlamaIndex，支持持久化
- **VectorSearchIndex**：轻量级 sentence-transformers 实现
- **HybridSearchEngine**：混合向量+关键词检索

## 开发注意事项

### 添加新功能时

1. 在 `src/` 下创建对应模块
2. 更新 `app.py` 中的 UI 调用
3. 添加类型注解和文档字符串
4. 测试边界情况（空数据库、大文件等）

### 性能优化点

- 向量索引构建较慢，考虑添加进度条
- 大文献库（>1000篇）建议使用 FAISS 替代原生检索
- LLM 调用可添加缓存避免重复请求

### 常见问题

- **LlamaIndex 导入失败**：降级到 `llama-index-core==0.10.x`
- **Word 文档解析错误**：确保是 `.docx` 格式，非 `.doc`
- **API 超时**：检查网络或降低 `max_tokens`

## 依赖管理

关键依赖版本锁定：

```
streamlit>=1.28.0
python-docx>=0.8.11
sentence-transformers>=2.2.0
llama-index-core>=0.10.0
scikit-learn>=1.3.0
faiss-cpu>=1.7.4
```

添加新依赖时更新 `requirements.txt` 并测试兼容性。
