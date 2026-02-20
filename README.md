# Paper Citation Inserter - 论文反插助手

基于AI的学术论文引用自动插入工具。用户上传Web of Science导出的文献库和待插入引用的草稿，系统自动为每句话匹配并插入最相关的参考文献。

## 功能特性

- 📚 **批量文献导入**: 支持Web of Science导出的Plain Text格式(.txt)
- 📝 **智能草稿分析**: 自动分割句子，提取关键信息
- 🔍 **句子级引用匹配**: 为每句话搜索最相关的1-3篇文献
- 🤖 **AI辅助匹配**: 使用大语言模型进行语义匹配
- 📄 **多格式输出**: 支持Word、Markdown、LaTeX格式
- ✏️ **交互式编辑**: 可手动调整每句话的引用

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行应用

```bash
streamlit run app.py
```

访问 `http://localhost:8501` 打开Web界面。

### 3. 使用流程

1. **Tab 1 - 导入文献库**: 批量上传Web of Science导出的txt文件
2. **Tab 2 - 上传草稿**: 上传写好但未插入引用的Word文档
3. **Tab 3 - 自动匹配**: 系统自动为每句话匹配相关文献
4. **Tab 4 - 结果导出**: 查看、调整引用并导出最终文档

## Web of Science文献导出指南

### 导出步骤

1. 在Web of Science中搜索并筛选文献
2. 选择需要导出的文献（建议50-500篇）
3. 点击"Export" → "Plain Text File"
4. 选择"Full Record"格式
5. 下载.txt文件

### 导出设置

- **文件格式**: Plain Text File
- **记录内容**: Full Record
- **编码**: UTF-8
- **每页记录数**: 500

## 项目结构

```
论文反插助手/
├── 📁 config/
│   └── config.yaml          # 配置文件
├── 📁 src/
│   ├── literature/
│   │   └── db_manager.py    # 文献数据库管理
│   ├── draft/
│   │   └── analyzer.py      # 草稿分析
│   ├── citation/
│   │   └── matcher.py       # 引用匹配
│   └── utils/
│       └── config.py        # 配置工具
├── 📁 data/                 # 数据库目录
├── 📁 output/               # 输出目录
├── 📁 uploads/              # 上传文件目录
├── app.py                   # Streamlit主界面
└── requirements.txt         # Python依赖
```

## 核心功能说明

### 1. 文献数据库管理

- 从WOS txt文件自动解析文献信息
- 生成标准citekey格式 (AuthorYear)
- SQLite数据库存储，支持快速检索
- 支持多文件批量导入

### 2. 草稿分析

- 读取Word文档内容
- 智能句子分割（考虑缩写、数字等）
- 提取每句话的关键词
- 识别引用位置

### 3. 引用匹配

- 基于关键词的初筛
- 基于语义的相关性计算
- 综合评分排序（相关性、引用数、时效性）
- AI辅助的精确匹配

### 4. 输出格式

- **Word**: 直接在原文中插入引用
- **Markdown**: 带引用标注的Markdown
- **LaTeX**: 生成LaTeX格式的引用命令

## 配置说明

编辑 `config/config.yaml` 自定义系统行为：

```yaml
# 引用格式
citation:
  style: "author-year"  # 或 "numbered"
  max_citations_per_sentence: 3
  
# 文献搜索
literature_search:
  default_limit: 10
  prioritize_highly_cited: true
```

## 技术依赖

- **Python 3.8+**
- **streamlit**: Web界面
- **python-docx**: Word文档处理
- **pandas**: 数据处理
- **numpy**: 数值计算
- **scikit-learn**: 文本相似度计算
- **openai/anthropic**: AI模型调用
- **sqlite3**: 数据库存储

## 使用建议

### 文献库建设

1. **主题相关**: 只导入与研究高度相关的文献
2. **质量优先**: 优先选择高影响力期刊论文
3. **数量适中**: 建议100-500篇，过多影响匹配速度
4. **时效性**: 包含经典文献和最新研究

### 草稿准备

1. 确保每句话表达清晰的观点或事实
2. 避免过长的复合句
3. 关键概念和术语使用标准表达
4. 段落结构清晰，逻辑连贯

### 引用匹配优化

1. 对于关键句子，可手动调整关键词
2. 检查匹配结果的相关性分数
3. 适当调整引用数量限制
4. 确保引用的多样性和平衡性

## 注意事项

- 文献库质量直接影响引用匹配效果
- 建议导入前检查WOS导出文件的完整性
- 草稿内容越清晰，匹配效果越好
- AI匹配结果建议人工复核

## 许可证

MIT License
