# GitHub Actions 打包教程

## 步骤1：创建GitHub账号
1. 访问 https://github.com
2. 点击 Sign up 注册账号
3. 验证邮箱

## 步骤2：创建仓库
1. 登录GitHub
2. 点击右上角 + 号 → New repository
3. Repository name: `paper-citation-assistant`
4. 选择 Public（免费）
5. 勾选 "Add a README file"
6. 点击 Create repository

## 步骤3：上传代码
在命令行中运行以下命令：

```bash
# 配置git（如果还没配置）
git config --global user.email "你的邮箱@example.com"
git config --global user.name "你的名字"

# 进入项目目录
cd "E:\AI_projects\论文反插助手"

# 删除之前失败的git（如果有）
rmdir /s /q .git 2>nul
del nul 2>nul
del 1.7.4 2>nul

# 重新初始化
git init

# 添加远程仓库（替换YOUR_USERNAME为你的GitHub用户名）
git remote add origin https://github.com/YOUR_USERNAME/paper-citation-assistant.git

# 添加文件（排除大文件）
git add .gitignore .github app.py src config requirements.txt README.md
git add start.bat build.py examples

# 提交
git commit -m "Initial commit"

# 推送
git branch -M main
git push -u origin main
```

## 步骤4：创建Workflow文件
在GitHub网页上操作：
1. 进入你的仓库
2. 点击 Actions 标签
3. 点击 "set up a workflow yourself"
4. 粘贴以下内容：

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

5. 点击 "Start commit" → "Commit new file"

## 步骤5：等待打包完成
1. 点击 Actions 标签
2. 等待工作流运行（约15-20分钟）
3. 状态变绿表示成功

## 步骤6：下载exe
1. 点击 Actions 标签
2. 点击最新的工作流运行
3. 在 Artifacts 部分下载 "论文反插助手-Windows"
4. 解压后就是打包好的exe

## 注意事项
- 首次运行需要15-20分钟
- GitHub Actions 免费版每月有2000分钟限制
- 下载的exe需要配合models文件夹使用（可以单独提供）

## 模型文件处理
由于模型文件太大（>100MB），GitHub不允许上传。
解决方案：
1. 打包时不包含模型
2. 用户首次运行时自动下载
3. 或者单独提供模型文件下载链接
