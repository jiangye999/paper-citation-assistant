# GitHub Actions 自动打包完整版指南

## 📦 打包内容

GitHub Actions 会打包**完整版本**，包含：

| 组件 | 大小 | 是否包含 |
|------|------|----------|
| Python 运行时 | ~15MB | ✅ |
| Streamlit + 依赖 | ~50MB | ✅ |
| 机器学习库 | ~80MB | ✅ |
| AI 模型文件 | ~200MB | ✅ |
| 项目代码 | ~1MB | ✅ |
| **总计** | **~350MB** | ✅ |

---

## 🚀 完整步骤

### 第一步：准备 GitHub 账号

1. 访问 https://github.com
2. 注册/登录账号

---

### 第二步：创建仓库

1. 访问 https://github.com/new
2. 填写信息：
   - **Repository name**: `paper-citation-inserter`（或你喜欢的名字）
   - **Description**: 论文反插助手 - AI 自动引用插入工具
   - **Public**: ✅ 公开（免费用户必须公开）
   - **Initialize**: ❌ 不要勾选

3. 点击 **Create repository**

---

### 第三步：上传代码到 GitHub

#### 方法 A: 使用 Git 命令行（推荐）

```bash
# 1. 进入项目目录
cd /d "E:\AI_projects\论文反插助手 - 副本"

# 2. 初始化 Git（如果还没有）
git init

# 3. 配置用户信息（第一次使用需要）
git config user.name "YourName"
git config user.email "your-email@example.com"

# 4. 添加所有文件
git add .

# 5. 提交
git commit -m "Initial commit - 论文反插助手"

# 6. 添加远程仓库（替换 YOUR_USERNAME 为你的 GitHub 用户名）
git remote add origin https://github.com/YOUR_USERNAME/paper-citation-inserter.git

# 7. 推送到 GitHub
git push -u origin main
```

#### 方法 B: 使用 GitHub Desktop（图形界面）

1. 下载 https://desktop.github.com
2. 安装后打开
3. File → Add Local Repository → 选择项目文件夹
4. 点击 Publish repository

#### 方法 C: 直接上传（适合小文件）

1. 在 GitHub 仓库页面
2. 点击 **uploading an existing file**
3. 拖拽文件上传
4. 点击 **Commit changes**

**注意**: 如果项目超过 100MB，某些文件可能无法直接上传，需要用 Git LFS 或命令行。

---

### 第四步：处理大文件（AI 模型）

由于模型文件较大（超过 100MB），需要使用 **Git LFS**：

```bash
# 安装 Git LFS
git lfs install

# 追踪模型文件
git lfs track "models/*"

# 创建 .gitattributes 文件
git add .gitattributes

# 添加模型文件
git add models/

# 提交
git commit -m "Add AI models with LFS"

# 推送
git push origin main
```

**或者**：修改 `.github/workflows/build.yml`，让 GitHub Actions 自动下载模型：

```yaml
# 在 Install dependencies 步骤后添加：
- name: Download AI Models
  run: |
    pip install sentence-transformers
    python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2', cache_folder='models')"
    python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('cross-encoder/ms-marco-MiniLM-L-6-v2', cache_folder='models/cross-encoder_ms-marco-MiniLM-L-6-v2')"
```

---

### 第五步：触发自动打包

#### 方式 A: 手动触发（推荐新手）

1. 访问你的 GitHub 仓库
2. 点击 **Actions** 标签
3. 点击 **Build and Release Windows EXE**
4. 点击 **Run workflow** 按钮
5. 选择分支（main）
6. 点击 **Run workflow**

#### 方式 B: 打标签自动触发

```bash
# 创建版本标签
git tag v1.0.0

# 推送标签（自动触发打包）
git push origin v1.0.0
```

---

### 第六步：等待打包完成

1. 在 **Actions** 标签页可以看到运行进度
2. 绿色 ✅ 表示成功，红色 ❌ 表示失败
3. 通常需要 **15-25 分钟**

**查看进度**：
- 点击运行记录
- 展开各个步骤查看详细信息
- Build EXE 步骤耗时最长

---

### 第七步：下载打包结果

#### 临时下载（5 天内）：

1. 点击成功的运行记录
2. 滚动到底部 **Artifacts**
3. 点击 `论文反插助手-Windows` 下载
4. 解压后即可使用

#### 永久下载（发布 Release）：

如果打了标签（如 v1.0.0）：

1. 访问仓库的 **Releases** 页面
2. 找到对应版本
3. 下载 Assets 中的文件
4. 永久保存

---

## ⚙️ 优化后的 Workflow 配置

如果现有配置打包失败，使用这个优化版本：

```yaml
name: Build Windows EXE (Full Version)

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

jobs:
  build:
    runs-on: windows-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.9'
        cache: 'pip'  # 缓存 pip 依赖
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pyinstaller
        pip install -r requirements.txt
    
    - name: Download AI Models
      run: |
        mkdir models
        python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2', cache_folder='models')"
        python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('cross-encoder/ms-marco-MiniLM-L-6-v2', cache_folder='models/cross-encoder_ms-marco-MiniLM-L-6-v2')"
        echo "Models downloaded successfully"
    
    - name: Build EXE
      run: |
        pyinstaller build_exe.spec --clean --noconfirm
      timeout-minutes: 30
    
    - name: Verify build
      run: |
        dir dist\论文反插助手
        echo "Build completed successfully"
    
    - name: Upload artifact
      uses: actions/upload-artifact@v4
      with:
        name: 论文反插助手-Windows-Full
        path: dist/论文反插助手
        retention-days: 30
    
    - name: Create Release
      if: startsWith(github.ref, 'refs/tags/v')
      uses: softprops/action-gh-release@v2
      with:
        files: dist/论文反插助手/*
        draft: false
        prerelease: false
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## 🔧 常见问题

### Q1: 推送失败，提示文件太大

**解决**：
```bash
# 使用 Git LFS
git lfs install
git lfs track "models/*"
git add .gitattributes
git add models/
git commit -m "Add models with LFS"
git push origin main
```

### Q2: Actions 运行失败

**检查**：
1. 点击失败的运行记录
2. 查看错误信息
3. 常见问题：
   - 依赖安装失败 → 检查 requirements.txt
   - 模型下载超时 → 使用镜像源
   - 打包超时 → 增加 timeout-minutes

### Q3: 打包后体积太大

**解决**：
- 正常现象，完整版约 300-400MB
- 如需减小，修改 spec 文件的 excludes 列表

### Q4: 用户反馈无法使用

**检查**：
1. 是否包含所有必要的文件
2. 模型文件是否正确
3. 查看控制台的错误信息

---

## 📊 GitHub Actions 限制

| 项目 | 免费账户 | 说明 |
|------|----------|------|
| 运行时间 | 2000 分钟/月 | 每次约 25 分钟 |
| 存储空间 | 500MB | 足够存放代码 |
| Artifact 大小 | 500MB | 足够打包结果 |
| 并发数 | 1 | 一次只能运行一个 |

**结论**：免费账户完全够用！

---

## 🎯 完整命令清单

```bash
# 1. 初始化 Git
cd /d "E:\AI_projects\论文反插助手 - 副本"
git init

# 2. 配置用户信息
git config user.name "YourName"
git config user.email "your-email@example.com"

# 3. 添加所有文件
git add .

# 4. 提交
git commit -m "Initial commit"

# 5. 添加远程仓库（替换 YOUR_USERNAME）
git remote add origin https://github.com/YOUR_USERNAME/paper-citation-inserter.git

# 6. 推送
git push -u origin main

# 7. 打标签（可选，用于发布 Release）
git tag v1.0.0
git push origin v1.0.0
```

---

## ✅ 检查清单

打包前确认：

- [ ] GitHub 账号已注册
- [ ] 仓库已创建
- [ ] 代码已推送到 GitHub
- [ ] `.github/workflows/build.yml` 存在
- [ ] `build_exe.spec` 配置正确
- [ ] `requirements.txt` 包含所有依赖

打包后确认：

- [ ] Actions 运行成功（绿色 ✅）
- [ ] Artifact 可下载
- [ ] 本地测试 exe 能正常运行
- [ ] 包含所有必要文件

---

## 📞 需要帮助？

如果遇到问题：
1. 查看 Actions 运行日志
2. 复制错误信息
3. 在 GitHub Issues 中提问

---

**现在就开始吧！第一步：创建 GitHub 仓库！**
