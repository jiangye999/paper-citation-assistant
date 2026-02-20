@echo off
chcp 65001 >nul
title 论文反插助手 - 桌面版

echo ========================================
echo   论文反插助手 - 桌面版
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python
    echo.
    echo 请先安装 Python 3.8+
    pause
    exit /b 1
)

echo [检查] 正在检查依赖...
pip show PyQt5 >nul 2>&1
if %errorlevel% neq 0 (
    echo [安装] 正在安装 PyQt5...
    pip install PyQt5 -q
)

echo [启动] 正在启动应用...
echo.

python desktop_app.py

pause
