@echo off
chcp 65001 >nul
echo ===========================================
echo 论文反插助手 - 启动脚本(国内镜像版)
echo ===========================================
echo.

REM 设置 HuggingFace 镜像源
echo [0/3] 设置镜像源...
set HF_ENDPOINT=https://hf-mirror.com
echo ✓ HF_ENDPOINT=%HF_ENDPOINT%
echo.

REM 清除 Python 缓存
echo [1/3] 清除缓存...
if exist "__pycache__" rmdir /s /q "__pycache__"
if exist "src\citation\__pycache__" rmdir /s /q "src\citation\__pycache__"
if exist "src\literature\__pycache__" rmdir /s /q "src\literature\__pycache__"
if exist "src\draft\__pycache__" rmdir /s /q "src\draft\__pycache__"
if exist "src\utils\__pycache__" rmdir /s /q "src\utils\__pycache__"
echo ✓ 缓存清除完成
echo.

REM 检查依赖
echo [2/3] 检查依赖...
python -c "import sentence_transformers" 2>nul
if %errorlevel% neq 0 (
    echo ⚠ sentence-transformers 未安装，正在安装...
    pip install sentence-transformers>=2.2.0 -q
)

python -c "import faiss" 2>nul
if %errorlevel% neq 0 (
    echo ⚠ faiss 未安装，正在安装...
    pip install faiss-cpu>=1.7.4 -q
)

echo ✓ 依赖检查完成
echo.

REM 启动应用
echo [3/3] 启动应用...
echo ✓ 启动中，请稍候...
echo.
echo 提示: 首次启动会下载AI模型(约100MB)，请耐心等待
echo      使用镜像源: https://hf-mirror.com
echo.

streamlit run app.py

pause
