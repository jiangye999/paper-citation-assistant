#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论文反插助手 - 打包脚本
一键打包为独立 exe 文件
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.absolute()
BUILD_DIR = PROJECT_ROOT / "build"
DIST_DIR = PROJECT_ROOT / "dist"
MODELS_DIR = PROJECT_ROOT / "models"


def check_pyinstaller():
    """检查 PyInstaller"""
    try:
        import PyInstaller

        print("✓ PyInstaller 已安装")
        return True
    except ImportError:
        print("⚠ PyInstaller 未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller", "-q"])
        print("✓ PyInstaller 安装完成")
        return True


def download_models():
    """下载 AI 模型"""
    print("\n[1/4] 下载 AI 模型...")

    model_dir = MODELS_DIR / "all-MiniLM-L6-v2"

    if model_dir.exists():
        print(f"✓ 模型已存在: {model_dir}")
        return True

    try:
        from sentence_transformers import SentenceTransformer

        # 设置镜像源
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

        print("  正在下载 all-MiniLM-L6-v2 模型 (约 100MB)...")
        print("  使用镜像源: https://hf-mirror.com")

        # 下载模型到项目目录
        model = SentenceTransformer("all-MiniLM-L6-v2", cache_folder=str(MODELS_DIR))

        # 重命名模型目录
        for item in MODELS_DIR.iterdir():
            if item.is_dir() and "sentence-transformers" in str(item):
                shutil.move(str(item), str(model_dir))
                break

        print(f"✓ 模型下载完成: {model_dir}")
        return True

    except Exception as e:
        print(f"✗ 模型下载失败: {e}")
        print("  请检查网络连接，或手动下载模型到 models/ 目录")
        return False


def prepare_resources():
    """准备资源文件"""
    print("\n[2/4] 准备资源文件...")

    # 创建必要的目录
    dirs = ["data", "uploads", "output", "config"]
    for dir_name in dirs:
        dir_path = PROJECT_ROOT / dir_name
        dir_path.mkdir(exist_ok=True)
        print(f"  ✓ 创建目录: {dir_name}")

    # 确保配置文件存在
    config_file = PROJECT_ROOT / "config" / "config.yaml"
    if not config_file.exists():
        config_file.write_text(
            """# 论文反插助手配置文件
citation:
  style: "author-year"
  max_citations_per_sentence: 3

literature_search:
  default_limit: 10
  prioritize_highly_cited: true
""",
            encoding="utf-8",
        )
        print(f"  ✓ 创建默认配置文件")

    print("✓ 资源文件准备完成")


def clean_build():
    """清理构建目录"""
    print("\n[3/4] 清理构建目录...")

    # 清理 Python 缓存
    cache_dirs = list(PROJECT_ROOT.rglob("__pycache__"))
    for cache_dir in cache_dirs:
        try:
            shutil.rmtree(cache_dir)
        except:
            pass

    # 清理旧的构建文件
    for dir_path in [BUILD_DIR / "exe", DIST_DIR]:
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                print(f"  ✓ 清理: {dir_path}")
            except:
                pass

    print("✓ 清理完成")


def build_exe():
    """构建 exe"""
    print("\n[4/4] 构建 exe...")

    # 构建命令
    spec_file = BUILD_DIR / "paper_citation_inserter.spec"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        str(spec_file),
        "--clean",
        "--noconfirm",
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(BUILD_DIR / "exe"),
    ]

    print(f"  执行: {' '.join(cmd)}")
    print("  这可能需要几分钟，请耐心等待...")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("✓ 构建成功！")
        exe_path = DIST_DIR / "论文反插助手" / "论文反插助手.exe"
        if exe_path.exists():
            print(f"\n✓ 可执行文件位置: {exe_path}")
            print(f"✓ 文件大小: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
        return True
    else:
        print("✗ 构建失败")
        print(
            "错误信息:",
            result.stderr[-500:] if len(result.stderr) > 500 else result.stderr,
        )
        return False


def create_launcher():
    """创建启动器"""
    print("\n[5/5] 创建启动器...")

    launcher_bat = DIST_DIR / "论文反插助手" / "启动.bat"
    launcher_bat.write_text(
        """@echo off
chcp 65001 >nul
echo 正在启动论文反插助手...
论文反插助手.exe
pause
""",
        encoding="gbk",
    )

    print(f"✓ 启动器创建完成: {launcher_bat}")


def main():
    """主函数"""
    print("=" * 60)
    print("论文反插助手 - 打包工具")
    print("=" * 60)

    # 检查 PyInstaller
    check_pyinstaller()

    # 下载模型
    if not download_models():
        print("\n模型下载失败，是否继续打包？(y/n): ", end="")
        response = input().strip().lower()
        if response != "y":
            print("已取消打包")
            return
        print("继续打包（将使用传统检索模式）...")

    # 准备资源
    prepare_resources()

    # 清理构建目录
    clean_build()

    # 构建 exe
    if build_exe():
        create_launcher()

        print("\n" + "=" * 60)
        print("打包完成！")
        print("=" * 60)
        print(f"\n输出目录: {DIST_DIR / '论文反插助手'}")
        print("\n使用方法:")
        print("  1. 将整个文件夹复制到目标电脑")
        print("  2. 双击 '启动.bat' 或 '论文反插助手.exe'")
        print("  3. 在浏览器中访问 http://localhost:8501")
        print("\n注意事项:")
        print("  - 首次启动可能需要几秒钟加载")
        print("  - 数据会保存在 data/ 目录中")
        print("=" * 60)
    else:
        print("\n✗ 打包失败，请查看错误信息")


if __name__ == "__main__":
    main()
