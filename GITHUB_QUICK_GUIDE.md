# GitHub Actions 快速打包指南

## 方法：复制模板仓库

### 步骤1：访问模板
1. 打开浏览器，访问：https://github.com/new
2. 创建一个新仓库：
   - Repository name: `paper-citation-assistant`
   - Description: 论文反插助手
   - 选择 **Public**
   - 勾选 **Add a README file**
   - 点击 **Create repository**

### 步骤2：上传必要文件
点击 `Add file` → `Upload files`，上传以下文件：
- `app.py`
- `requirements.txt`
- `README.md`
- `src/` 文件夹（整个文件夹打包成zip上传）

### 步骤3：创建工作流
点击 `Add file` → `Create new file`

**文件名**：`.github/workflows/build.yml`

**内容**：
```yaml
name: Build Windows EXE

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  build:
    runs-on: windows-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pyinstaller
        pip install -r requirements.txt
    
    - name: Build EXE
      run: |
        pyinstaller app.py --name "论文反插助手" --onedir --console -y
      timeout-minutes: 30
    
    - name: Upload artifact
      uses: actions/upload-artifact@v3
      with:
        name: 论文反插助手-Windows
        path: dist/论文反插助手
        retention-days: 30
```

点击 **Commit new file**

### 步骤4：等待打包
1. 点击顶部 **Actions** 标签
2. 等待工作流运行（显示黄色圆点）
3. 约15-20分钟后变成绿色勾号 ✅

### 步骤5：下载exe
1. 点击最新的成功运行记录
2. 页面底部找到 **Artifacts**
3. 点击 **论文反插助手-Windows** 下载
4. 解压zip文件，里面就是打包好的exe

---

## ⚠️ 重要提示

由于模型文件太大（>100MB），GitHub不允许上传。你有两个选择：

### 选择A：打包不包含模型（推荐）
用户首次使用时自动下载模型（需要联网）

### 选择B：单独提供模型
打包后，把 `models/` 文件夹单独复制到exe同目录

---

## 📦 需要上传的文件清单

在你创建好GitHub仓库后，上传以下文件：

```
必需文件：
├── app.py
├── requirements.txt
├── README.md
├── .github/workflows/build.yml
├── src/
│   ├── __init__.py
│   ├── literature/
│   ├── draft/
│   ├── citation/
│   └── utils/
├── config/
│   └── config.yaml
└── data/
    └── literature.db
```

**不需要上传的**（太大）：
- `models/` 文件夹（AI模型，>100MB）
- `uploads/` 文件夹（用户上传文件）
- `output/` 文件夹（输出文件）

---

## 🎯 操作流程总结

1. 注册GitHub账号（2分钟）
2. 创建仓库（1分钟）
3. 上传代码文件（3分钟）
4. 创建工作流文件（1分钟）
5. 等待15-20分钟自动打包
6. 下载exe（1分钟）

**总时间：约25-30分钟**

---

## ❓ 遇到问题怎么办？

如果GitHub Actions打包失败：
1. 点击 Actions 标签
2. 点击失败的运行记录
3. 查看错误日志
4. 把错误信息发给我，我帮你解决

**或者直接用Python运行**（应急方案）：
```bash
pip install -r requirements.txt
streamlit run app.py
```
