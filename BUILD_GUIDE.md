# 论文反插助手 - 打包指南

本文档介绍如何将应用打包为独立的 Windows exe 文件，方便分发给没有 Python 环境的用户使用。

## 📦 打包前准备

### 1. 安装打包依赖

```bash
pip install pyinstaller
```

### 2. 确保应用可正常运行

```bash
python start.py
```

确认应用能正常启动后再进行打包。

## 🚀 一键打包

最简单的打包方式（全自动）：

```bash
python build.py
```

此命令会：
1. 自动下载 AI 模型（约 100MB）
2. 准备资源文件
3. 清理构建缓存
4. 构建 exe 文件
5. 创建启动器

**输出位置**: `dist/论文反插助手/`

## 📋 打包结构

打包后的目录结构：

```
dist/论文反插助手/
├── 论文反插助手.exe      # 主程序
├── 启动.bat              # 便捷启动器
├── config/               # 配置文件目录
├── data/                 # 数据库目录
├── models/               # AI 模型目录
│   └── all-MiniLM-L6-v2/ # 向量模型
├── uploads/              # 上传文件目录
└── output/               # 输出文件目录
```

## 🎯 分发给用户

### 方式1：文件夹形式（推荐）

将整个 `论文反插助手` 文件夹压缩为 zip/rar，用户解压后双击 `启动.bat` 即可运行。

**优点**: 
- 用户可以保存数据（data/ 目录）
- 可以查看生成的文件（output/ 目录）
- 文件体积小

### 方式2：安装包形式

使用 Inno Setup 或 NSIS 创建安装程序。

**推荐工具**: [Inno Setup](https://jrsoftware.org/isinfo.php)

**示例脚本**: `build/installer.iss`

## ⚙️ 打包配置说明

### PyInstaller 配置

主要配置文件: `build/paper_citation_inserter.spec`

关键配置项：

```python
# 包含的数据文件
datas=[
    ('config/config.yaml', 'config'),
    ('models/all-MiniLM-L6-v2', 'models/all-MiniLM-L6-v2'),  # AI 模型
    ('data', 'data'),
    ('uploads', 'uploads'),
    ('output', 'output'),
]

# 隐藏的导入（PyInstaller 可能检测不到的模块）
hiddenimports=[
    'streamlit',
    'pandas',
    'sklearn',
    'sentence_transformers',
    'faiss',
    # ... 其他模块
]

# 排除的不必要库（减小体积）
excludes=[
    'matplotlib',
    'PIL',
    'tkinter',
    'PyQt5',
    # ... 其他不需要的库
]
```

### 模型处理

**关键修改**: `src/citation/search_engine.py`

代码已修改为优先从项目目录加载模型：

```python
def _get_local_model_path(self) -> str:
    # 优先检查项目目录下的 models 文件夹（打包exe时使用）
    project_model_path = Path(__file__).parent.parent.parent / "models" / "all-MiniLM-L6-v2"
    if project_model_path.exists():
        return str(project_model_path)
    
    # 其次检查用户缓存目录
    # ...
```

这样打包后的 exe 可以直接使用内置的模型，无需联网下载。

## 📊 包大小优化

### 当前体积估算

| 组件 | 大小 |
|------|------|
| Python 运行时 | ~15 MB |
| Streamlit + 依赖 | ~50 MB |
| 机器学习库 (sklearn, numpy等) | ~80 MB |
| Sentence-Transformers | ~30 MB |
| AI 模型 (all-MiniLM-L6-v2) | ~90 MB |
| 项目代码 | ~1 MB |
| **总计** | **~250-300 MB** |

### 减小体积的方法

1. **使用 UPX 压缩**（已默认启用）
   ```python
   upx=True
   ```

2. **排除不必要的库**
   - 已在 spec 文件中排除了 matplotlib、PIL、tkinter 等

3. **单文件 vs 文件夹**
   - 当前使用文件夹模式（更快启动，更小体积）
   - 如需单文件，修改 `console=False` 并启用 `--onefile`

## 🔧 高级配置

### 自定义图标

将图标文件放到 `assets/icon.ico`，打包时会自动使用。

### 隐藏控制台窗口

修改 `build/paper_citation_inserter.spec`：

```python
exe = EXE(
    ...
    console=False,  # 改为 False 隐藏控制台
    ...
)
```

⚠️ 注意：如果隐藏控制台，出错时无法看到错误信息，建议保留。

### 添加版本信息

在 spec 文件中添加：

```python
exe = EXE(
    ...
    version='build/version.txt',
    ...
)
```

创建 `build/version.txt`：

```
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    ...
  )
)
```

## 🐛 常见问题

### 1. 打包后启动失败

**症状**: 双击 exe 无反应或闪退

**解决**:
- 检查 `data/` 目录是否有写入权限
- 查看控制台错误信息（保留 `console=True`）
- 确保所有数据文件都包含在打包中

### 2. 模型加载失败

**症状**: 提示 "模型未找到" 或 "无法连接 HuggingFace"

**解决**:
- 确保 `models/all-MiniLM-L6-v2/` 目录已打包
- 检查 `_get_local_model_path()` 是否正确找到模型路径

### 3. 文件体积过大

**解决**:
- 确认 `excludes` 列表已排除不必要的库
- 使用 UPX 压缩（自动启用）
- 考虑分离模型文件（让用户首次运行时下载）

### 4. 杀毒软件误报

**原因**: PyInstaller 打包的程序有时会被误报为病毒

**解决**:
- 使用 `--onefile` 改为单文件模式
- 添加数字签名（需要证书）
- 向杀毒软件厂商提交误报申诉

## 📝 手动打包步骤（不使用 build.py）

如果 `build.py` 失败，可以手动执行：

```bash
# 1. 安装依赖
pip install pyinstaller

# 2. 下载模型
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2', cache_folder='models')"

# 3. 创建目录
mkdir data uploads output config

# 4. 清理缓存
rmdir /s /q __pycache__
rmdir /s /q src\citation\__pycache__
rmdir /s /q src\literature\__pycache__

# 5. 执行打包
pyinstaller build/paper_citation_inserter.spec --clean --noconfirm

# 6. 检查输出
ls dist/论文反插助手/
```

## 🎁 发布清单

打包完成后，检查以下内容：

- [ ] exe 文件可以正常启动
- [ ] 可以导入文献
- [ ] 可以上传草稿
- [ ] 可以进行引用匹配
- [ ] 可以导出文档
- [ ] 数据可以保存（重启后数据还在）
- [ ] 包含所有必要的目录（config/, data/, uploads/, output/）

## 💡 最佳实践

1. **版本控制**: 每次发布前更新版本号
2. **测试环境**: 在干净的 Windows 虚拟机中测试
3. **增量更新**: 如果只有代码更新，可以让用户保留 data/ 目录
4. **文档**: 提供简单的使用说明（README.txt）

## 📞 技术支持

打包过程中遇到问题：

1. 查看 PyInstaller 日志：`build/exe/` 目录下的日志文件
2. 使用 `--debug` 参数重新打包
3. 检查是否缺少 hiddenimports

---

**注意**: 首次打包可能需要 5-10 分钟，请耐心等待。
