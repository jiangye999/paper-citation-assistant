@echo off
chcp 65001 >nul
title 论文反插助手 - 打包工具

echo ========================================
echo   论文反插助手 - 低配置打包工具
echo ========================================
echo.
echo 此脚本将创建精简版安装包
echo 优点：打包快、内存占用低
echo 缺点：用户首次使用需下载模型
echo.
echo 按任意键开始打包...
pause >nul
echo.

python build_lite.py

echo.
echo ========================================
echo 打包完成!
echo ========================================
echo.
echo 输出目录：dist\论文反插助手_lite
echo.
pause
