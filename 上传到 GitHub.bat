@echo off
chcp 65001 >nul
title 上传代码到 GitHub

echo ========================================
echo   论文反插助手 - 上传到 GitHub
echo ========================================
echo.
echo 此脚本将上传所有文件到你的 GitHub 仓库
echo 仓库：https://github.com/jiangye999/paper-citation-assistant
echo.

REM 检查 Git
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Git
    echo.
    echo 请先安装 Git: https://git-scm.com/download/win
    echo 安装后重新运行此脚本
    pause
    exit /b 1
)

echo [1/5] Git 已安装
git --version

REM 检查是否在 Git 仓库中
if not exist .git (
    echo.
    echo [2/5] 初始化 Git 仓库...
    git init
) else (
    echo.
    echo [2/5] Git 仓库已存在
)

REM 配置用户信息
echo.
echo [3/5] 配置 Git 用户信息...
git config user.name jiangye999
echo 用户名设置为：jiangye999

REM 添加远程仓库（如果不存在）
git remote get-url origin >nul 2>nul
if %errorlevel% neq 0 (
    echo.
    echo 添加远程仓库...
    git remote add origin https://github.com/jiangye999/paper-citation-assistant.git
    echo 远程仓库已添加
) else (
    echo.
    echo 远程仓库已配置
)

REM 添加所有文件
echo.
echo [4/5] 添加文件到 Git...
git add .
echo 文件添加完成

REM 查看状态
echo.
echo 即将提交的文件:
git status --short

REM 提交
echo.
echo [5/5] 提交更改...
git commit -m Upload complete project with all source files
if %errorlevel% equ 0 (
    echo 提交成功
) else (
    echo 没有需要提交的文件或提交失败
)

REM 推送
echo.
echo ========================================
echo 推送到 GitHub...
echo ========================================
echo.
echo 注意：
echo - 如果文件较大，可能需要几分钟
echo - 如果提示大文件错误，请运行：git lfs install
echo.
echo 按任意键开始推送...
pause >nul

git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   上传成功！
    echo ========================================
    echo.
    echo 请访问你的 GitHub 仓库:
    echo https://github.com/jiangye999/paper-citation-assistant
    echo.
    echo 下一步:
    echo 1. 访问上述链接
    echo 2. 点击 Actions 标签
    echo 3. 点击 Run workflow 开始打包
    echo.
) else (
    echo.
    echo ========================================
    echo   推送失败
    echo ========================================
    echo.
    echo 可能的原因:
    echo 1. 网络连接问题
    echo 2. 需要 Git LFS (运行：git lfs install)
    echo 3. 仓库权限问题
    echo.
    echo 错误详情:
    git push -u origin main 2>&1
)

echo.
pause
