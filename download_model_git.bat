@echo off
chcp 65001 >nul
echo ===========================================
echo 使用 Git 下载 HuggingFace 模型
echo ===========================================
echo.

REM 设置代理（根据检测到的端口）
echo [1/3] 设置代理...
set HTTP_PROXY=http://127.0.0.1:7897
set HTTPS_PROXY=http://127.0.0.1:7897
echo 代理: %HTTP_PROXY%
echo.

REM 创建目录
echo [2/3] 创建目录...
if not exist "models" mkdir models
cd models
echo.

REM 使用 Git 克隆模型
echo [3/3] 下载模型...
echo 正在从 HuggingFace 下载 all-MiniLM-L6-v2...
echo 文件大小约 100MB，请耐心等待...
echo.

if exist "all-MiniLM-L6-v2" (
    echo 目录已存在，更新中...
    cd all-MiniLM-L6-v2
    git pull
) else (
    git clone https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
)

echo.
echo ===========================================
if %errorlevel% == 0 (
    echo [OK] 模型下载成功！
    echo.
    echo 模型位置: models\all-MiniLM-L6-v2\
    echo.
    echo 现在可以打包完整版 exe:
    echo   python build.py
) else (
    echo [ERROR] 下载失败
    echo.
    echo 可能原因:
    echo   1. VPN 未正确连接
    echo   2. Git LFS 未安装
    echo.
    echo 请尝试:
    echo   1. 确认 VPN 正常工作
    echo   2. 安装 Git LFS: git lfs install
    echo   3. 使用无模型版本: python build_no_model.py
)
echo ===========================================

pause
