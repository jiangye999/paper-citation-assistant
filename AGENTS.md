# AGENTS.md - 论文反插助手开发指南

## 项目概述

基于 AI 的学术论文引用自动插入工具，使用 Streamlit 构建 Web 界面，支持从 Web of Science 导入文献并为草稿自动匹配引用。

**技术栈**: Python 3.8+, Streamlit, SQLite, FAISS, Sentence-Transformers

## 构建/运行命令

```bash
# 安装依赖
pip install -r requirements.txt

# 运行 Web 应用
streamlit run app.py

# 运行桌面应用（PyQt5）
python desktop_app.py

# 测试
python test_integration.py
```

## 代码检查

```bash
pip install ruff
ruff check .
ruff check --fix .
ruff format .
```

## 项目结构

```
论文反插助手/
├── app.py                          # Streamlit 主入口
├── desktop_app.py                  # PyQt5 桌面版
├── test_integration.py             # 集成测试
├── config/config.yaml              # 配置文件
├── src/
│   ├── literature/db_manager.py    # 文献数据库管理
│   ├── draft/analyzer.py           # Word 文档分析
│   └── citation/
│       ├── search_engine.py        # 混合搜索引擎
│       ├── ai_matcher.py           # AI 语义匹配
│       └── matcher.py              # 基础匹配
├── data/                           # 数据库和向量索引
├── uploads/                        # 上传文件
└── output/                         # 输出文档
```

## 代码风格指南

### Python 规范

- **类型注解**: 所有函数参数和返回值必须添加类型注解
- **文档字符串**: 使用 Google 风格 docstring（Args/Returns/Raises）
- **导入排序**: 标准库 → 第三方库 → 本地模块，每组空一行
- **行长度**: 不超过 100 字符
- **数据类**: 优先使用 `@dataclass`

### 命名约定

| 类型 | 风格 | 示例 |
|------|------|------|
| 类名 | `PascalCase` | `LiteratureDatabaseManager` |
| 函数/变量 | `snake_case` | `get_statistics()` |
| 常量 | `UPPER_SNAKE_CASE` | `DEFAULT_LIMIT` |
| 私有方法 | `_leading_underscore` | `_load_config()` |

### 导入示例

```python
# 标准库
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

# 第三方库
import streamlit as st
import pandas as pd
import numpy as np

# 本地模块
from src.literature.db_manager import LiteratureDatabaseManager, Paper
```

### 错误处理

```python
# 必须捕获具体异常，禁止裸 except
try:
    result = risky_operation()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    return default_value
except FileNotFoundError as e:
    logger.error(f"File not found: {e}")
    raise
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    raise
```

### 数据库操作

- 使用上下文管理器确保连接关闭
- SQL 参数化查询，禁止字符串拼接
- 批量操作使用事务

```python
def get_paper_by_id(self, paper_id: int) -> Optional[Paper]:
    conn = sqlite3.connect(self.db_path)
    try:
        cursor = conn.execute(
            "SELECT * FROM papers WHERE id = ?", (paper_id,)
        )
        row = cursor.fetchone()
        return Paper(*row) if row else None
    finally:
        conn.close()
```

### AI API 调用

- 所有 LLM 调用必须有超时设置（默认 30s）
- 实现指数退避重试机制（最多 3 次）
- 响应解析失败时返回优雅降级结果

## 核心模块

### db_manager.py
- 解析 Web of Science Plain Text 格式
- 自动生成 citekey（AuthorYear 格式）
- 支持增量导入（基于 DOI/WOS ID 去重）

### search_engine.py
- **QueryExpander**: LLM 查询扩展
- **多路召回**: 向量 + 关键词检索
- **Cross-encoder**: 重排序
- **MMR**: 多样性算法

### ai_matcher.py
- AI 辅助语义匹配
- 两步筛选法：语义筛选 → 加权排序

## 开发注意事项

### 添加新功能

1. 在 `src/` 下创建对应模块
2. 更新 UI 调用（app.py 或 desktop_app.py）
3. 添加类型注解和文档字符串
4. 测试边界情况
5. 更新 requirements.txt

### 性能优化

- 向量索引构建添加进度条
- 大文献库（>1000 篇）使用 FAISS
- LLM 调用添加缓存
- 查询扩展使用 LRU 缓存

### 常见问题

- **LlamaIndex 导入失败**: 降级到 `llama-index-core==0.10.x`
- **Word 文档解析错误**: 确保是 `.docx` 格式
- **API 超时**: 检查网络或降低 `max_tokens`
- **FAISS 加载失败**: 确认 `faiss-cpu` 已安装

## 依赖管理

### 关键依赖

```
PyQt5>=5.15.0                # 桌面界面
streamlit>=1.28.0            # Web 界面
python-docx>=0.8.11          # Word 处理
pandas>=1.5.0                # 数据处理
sentence-transformers>=2.2.0 # 向量嵌入
faiss-cpu>=1.7.4             # 向量检索
```

### 添加新依赖

1. 评估必要性
2. 添加到 requirements.txt
3. 测试兼容性

## 测试

```bash
# 集成测试
python test_integration.py

# 模块导入测试
python -c "from src.literature.db_manager import LiteratureDatabaseManager; print('OK')"
python -c "from src.draft.analyzer import DraftAnalyzer; print('OK')"
python -c "from src.citation.search_engine import HybridSearchEngine; print('OK')"
```

## 构建打包

```bash
# 完整版打包
python build.py

# 轻量版打包
python build_lite.py

# 输出在 dist/ 目录
```

## Git 提交规范

```
feat: 新功能
fix: 修复错误
docs: 文档更新
refactor: 重构
test: 测试
chore: 构建/依赖
```

## 资源链接

- 项目仓库：https://github.com/jiangye99/paper-citation-assistant
- Streamlit 文档：https://docs.streamlit.io
- FAISS: https://faiss.ai
