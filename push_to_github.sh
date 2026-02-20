#!/bin/bash
# 一键推送到GitHub脚本

echo "=========================================="
echo "论文反插助手 - GitHub一键推送"
echo "=========================================="
echo ""

# 配置你的GitHub用户名
GITHUB_USERNAME="jiangye999"
REPO_NAME="paper-citation-assistant"

echo "[1/5] 清理临时文件..."
rm -f nul 2>/dev/null
rm -f 1.7.4 2>/dev/null
rm -rf .git 2>/dev/null
rm -rf build 2>/dev/null
rm -rf dist 2>/dev/null
rm -f *.spec 2>/dev/null

echo "[2/5] 初始化Git..."
git init
git config user.email "deploy@example.com"
git config user.name "Deploy Script"

echo "[3/5] 添加远程仓库..."
git remote add origin https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git

echo "[4/5] 添加文件..."
git add .gitignore
# 逐个添加关键文件，避免大文件
git add app.py requirements.txt README.md
git add src/ config/ data/
git add .github/workflows/
git add *.md

echo "[5/5] 提交并推送..."
git commit -m "Initial commit for GitHub Actions build"
git branch -M main

echo ""
echo "=========================================="
echo "正在推送到GitHub..."
echo "=========================================="
echo ""

# 推送（会提示输入用户名密码）
git push -u origin main

echo ""
echo "=========================================="
if [ $? -eq 0 ]; then
    echo "✅ 推送成功！"
    echo ""
    echo "接下来："
    echo "1. 打开 https://github.com/${GITHUB_USERNAME}/${REPO_NAME}"
    echo "2. 点击 Actions 标签"
    echo "3. 等待15-20分钟自动打包"
    echo "4. 下载打包好的exe"
    echo "=========================================="
else
    echo "❌ 推送失败"
    echo "请检查："
    echo "  1. GitHub用户名是否正确: ${GITHUB_USERNAME}"
    echo "  2. 仓库是否存在: ${REPO_NAME}"
    echo "  3. 网络连接是否正常"
    echo "=========================================="
fi

read -p "按回车键退出..."
