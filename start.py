#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论文反插助手启动脚本
自动清除缓存、检查依赖、启动应用
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def clear_cache():
    """清除 Python 缓存"""
    print("[1/3] 清除缓存...")

    cache_dirs = [
        "__pycache__",
        "src/__pycache__",
        "src/citation/__pycache__",
        "src/literature/__pycache__",
        "src/draft/__pycache__",
        "src/utils/__pycache__",
    ]

    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print(f"  ✓ 已清除: {cache_dir}")
            except Exception as e:
                print(f"  ⚠ 清除失败 {cache_dir}: {e}")

    print("✓ 缓存清除完成\n")


def check_dependencies():
    """检查并安装依赖"""
    print("[2/3] 检查依赖...")

    dependencies = [
        ("sentence_transformers", "sentence-transformers>=2.2.0"),
        ("faiss", "faiss-cpu>=1.7.4"),
    ]

    for module, package in dependencies:
        try:
            __import__(module)
            print(f"  ✓ {module} 已安装")
        except ImportError:
            print(f"  ⚠ {module} 未安装，正在安装 {package}...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", package, "-q"], check=True
            )
            print(f"  ✓ {package} 安装完成")

    print("✓ 依赖检查完成\n")


def start_app():
    """启动 Streamlit 应用"""
    print("[3/3] 启动应用...")
    print("✓ 启动中，请稍候...")
    print("\n" + "=" * 50)
    print("提示: 首次启动会下载AI模型(约100MB)")
    print("      使用镜像源:", os.environ.get("HF_ENDPOINT", "https://hf-mirror.com"))
    print("=" * 50)
    print("\n应用启动后，请在浏览器中访问:")
    print("  http://localhost:8501")
    print("=" * 50 + "\n")

    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\n\n应用已停止")


def setup_env():
    """设置环境变量"""
    print("[0/4] 设置环境变量...")

    # 设置 HuggingFace 镜像源
    if not os.environ.get("HF_ENDPOINT"):
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

    print(f"  ✓ HF_ENDPOINT={os.environ.get('HF_ENDPOINT')}")
    print("✓ 环境变量设置完成\n")


def main():
    """主函数"""
    print("=" * 50)
    print("论文反插助手 - 启动脚本")
    print("=" * 50)
    print()

    # 切换到脚本所在目录
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)

    setup_env()
    clear_cache()
    check_dependencies()
    start_app()


if __name__ == "__main__":
    main()
