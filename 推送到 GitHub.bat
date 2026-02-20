@echo off
chcp 65001 >nul
title 推送到 GitHub

echo ========================================
echo   推送到 GitHub
echo ========================================
echo.

cd /d "E:\AI_projects\论文反插助手 - 副本"

echo [1/3] 添加文件...
git add -A

echo [2/3] 提交更改...
git commit -m "Add PyQt5 desktop version"

echo [3/3] 推送到 GitHub...
git push origin main

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   推送成功！
    echo ========================================
    echo.
    echo 现在可以打包了：
    echo 1. 访问：https://github.com/jiangye999/paper-citation-assistant/actions
    echo 2. 点击：Build Windows EXE (Simple)
    echo 3. 点击：Run workflow
    echo 4. 等待 25-35 分钟
    echo 5. 下载 EXE 文件
) else (
    echo.
    echo ========================================
    echo   推送失败
    echo ========================================
    echo.
    echo 可能是网络问题，请尝试：
    echo 1. 检查网络连接
    echo 2. 稍后重试
    echo 3. 使用手机热点
)

pause
