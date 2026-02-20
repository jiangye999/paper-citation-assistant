# 论文反插助手 - 低配置打包指南

## 🎯 适用场景

**如果你遇到以下问题，请使用本方案：**

- ✅ 内存 ≤ 8GB
- ✅ 标准版 `build.py` 打包失败
- ✅ 网络速度慢，模型下载失败
- ✅ 打包过程中电脑卡顿严重
- ✅ PyInstaller 报错内存不足

---

## 📦 方案对比

| 方案 | 标准版 | 精简版（推荐低配置） |
|------|--------|---------------------|
| **打包文件** | `build.py` | `build_lite.py` |
| **包含模型** | ✅ 是（200MB+） | ❌ 否 |
| **输出体积** | ~300MB | ~100MB |
| **内存需求** | 4-8GB | 2-4GB |
| **打包时间** | 10-20 分钟 | 5-10 分钟 |
| **成功率** | 低配置易失败 | 高 |

---

## 🚀 一键打包（推荐）

### 方法 1: 双击批处理文件

```
双击运行：一键打包_lite.bat
```

### 方法 2: 命令行运行

```bash
cd "E:\AI_projects\论文反插助手 - 副本"
python build_lite.py
```

---

## 📋 打包流程

### 步骤 1: 检查环境
```
[0/3] 检查环境
✓ PyInstaller 已安装
```

### 步骤 2: 构建精简版
```
[1/3] 构建精简版（不含 AI 模型）
✓ 精简版 spec 已创建
开始构建... (3-8 分钟)
✓ 构建成功！
```

### 步骤 3: 创建启动器
```
[2/3] 创建启动器
✓ 启动器已创建
✓ 使用说明已创建
```

### 步骤 4: 完成
```
[3/3] 创建批处理文件
🎉 打包完成！
输出目录：dist/论文反插助手_lite
```

---

## 📂 打包后结构

```
dist/论文反插助手_lite/
├── 论文反插助手_lite.exe   # 主程序（~100MB）
├── 启动.bat                # 便捷启动器
├── 使用说明.txt            # 用户指南
├── config/                 # 配置文件
├── data/                   # 数据库目录
├── uploads/                # 上传文件目录
└── output/                 # 输出文件目录
```

**注意**：精简版**不包含** `models/` 目录，用户首次使用时会自动下载。

---

## 👥 用户使用方法

### 方式 1: 自动下载（推荐）

1. 用户双击 `启动.bat` 或 `论文反插助手_lite.exe`
2. 首次运行时，系统自动下载 AI 模型（约 100MB）
3. 下载完成后正常使用

### 方式 2: 手动下载（网络差时）

如果用户网络不好，你可以：

**选项 A**: 提前下载好模型，一起打包
```bash
# 在你电脑上下载模型
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2', cache_folder='models')"

# 然后重新运行标准版 build.py
python build.py
```

**选项 B**: 指导用户手动下载
```
1. 访问：https://hf-mirror.com/sentence-transformers/all-MiniLM-L6-v2
2. 下载模型文件
3. 解压到程序目录的 models/all-MiniLM-L6-v2/ 文件夹
```

---

## 🔧 故障排除

### 问题 1: PyInstaller 未安装

**错误**: `No module named 'PyInstaller'`

**解决**:
```bash
pip install pyinstaller
```

### 问题 2: 内存不足

**错误**: `MemoryError` 或打包过程中电脑卡死

**解决**:
1. 关闭所有其他程序（浏览器、Office 等）
2. 重启电脑后重试
3. 如果还是失败，考虑升级内存或换电脑

### 问题 3: 构建时间过长

**现象**: 超过 30 分钟还在构建

**解决**:
- 正常现象，大项目可能需要 20-40 分钟
- 查看控制台是否有进度输出
- 如果完全无响应超过 10 分钟，按 Ctrl+C 取消后重试

### 问题 4: 用户反馈模型下载失败

**解决**:
```bash
# 方法 1: 使用镜像源
set HF_ENDPOINT=https://hf-mirror.com
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2', cache_folder='models')"

# 方法 2: 手动下载
# 访问 https://hf-mirror.com 下载模型文件
```

---

## 📊 体积优化建议

### 如果还需要更小体积：

1. **排除更多库** - 编辑 `build/lite.spec`：
```python
excludes=[
    'matplotlib',
    'scipy',  # 如果不需要高级数学功能
    'nltk',   # 如果不需要 NLTK 功能
    ...
]
```

2. **使用 UPX 压缩** - 已默认启用

3. **单文件模式** - 修改 spec：
```python
exe = EXE(
    ...
    console=True,
    # 单文件模式启动慢，不推荐
)
```

---

## ✅ 打包检查清单

打包完成后，请检查：

- [ ] `dist/论文反插助手_lite/论文反插助手_lite.exe` 存在
- [ ] 文件大小约 80-120MB
- [ ] 包含 `启动.bat`
- [ ] 包含 `使用说明.txt`
- [ ] 包含 `config/`、`data/`、`uploads/`、`output/` 目录
- [ ] 运行 exe 能正常启动（测试！）
- [ ] 浏览器能访问 `http://localhost:8501`

---

## 💡 分发建议

### 给用户的压缩包应包含：

```
论文反插助手_用户版.zip
└── 论文反插助手_lite/
    ├── 论文反插助手_lite.exe
    ├── 启动.bat
    ├── 使用说明.txt
    ├── config/
    ├── data/
    ├── uploads/
    └── output/
```

### 附加说明：

在压缩包里加一个 `README.txt`：
```
欢迎使用论文反插助手！

启动方法：
1. 双击 "启动.bat"
2. 浏览器自动打开 http://localhost:8501

首次使用：
- 系统会自动下载 AI 模型（约 100MB）
- 请保持网络连接
- 如果下载失败，联系技术支持

数据保存：
- 所有数据保存在 data/ 目录
- 导出文件在 output/ 目录
```

---

## 📞 技术支持

如果打包还是失败，提供以下信息：

1. **电脑配置**：内存大小、CPU 型号
2. **Python 版本**：`python --version`
3. **错误信息**：控制台的完整错误输出
4. **PyInstaller 版本**：`pyinstaller --version`

---

**最后提醒**：精简版是为了低配置电脑设计的妥协方案。如果条件允许，建议使用标准版 `build.py` 打包，包含模型的文件用户体验更好。
