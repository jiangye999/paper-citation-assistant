#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论文反插助手 - 无模型打包脚本
适用于无法下载 HuggingFace 模型的环境
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.absolute()
BUILD_DIR = PROJECT_ROOT / "build"
DIST_DIR = PROJECT_ROOT / "dist"


def check_pyinstaller():
    try:
        import PyInstaller

        print("✓ PyInstaller 已安装")
        return True
    except ImportError:
        print("⚠ PyInstaller 未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller", "-q"])
        return True


def prepare_resources():
    print("\n[1/3] 准备资源文件...")

    dirs = ["data", "uploads", "output", "config"]
    for dir_name in dirs:
        dir_path = PROJECT_ROOT / dir_name
        dir_path.mkdir(exist_ok=True)
        print(f"  ✓ 创建目录: {dir_name}")

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
    print("\n[2/3] 清理构建目录...")

    cache_dirs = list(PROJECT_ROOT.rglob("__pycache__"))
    for cache_dir in cache_dirs:
        try:
            shutil.rmtree(cache_dir)
        except:
            pass

    for dir_path in [BUILD_DIR / "exe", DIST_DIR]:
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                print(f"  ✓ 清理: {dir_path}")
            except:
                pass

    print("✓ 清理完成")


def build_exe():
    print("\n[3/3] 构建 exe...")

    spec_file = BUILD_DIR / "paper_citation_inserter_no_model.spec"

    if not spec_file.exists():
        print("⚠ 创建打包配置...")
        create_spec_file(spec_file)

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

    print(f"  这可能需要几分钟，请耐心等待...")

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
            "错误:", result.stderr[-500:] if len(result.stderr) > 500 else result.stderr
        )
        return False


def create_spec_file(spec_path):
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

project_root = Path(os.path.abspath(SPECPATH)).parent

data_files = [
    ('config/config.yaml', 'config'),
    ('data', 'data'),
    ('uploads', 'uploads'),
    ('output', 'output'),
]

a = Analysis(
    ['app.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=data_files,
    hiddenimports=[
        'streamlit',
        'streamlit.runtime.scriptrunner.script_runner',
        'pandas',
        'pandas._libs.tslibs.base',
        'numpy',
        'docx',
        'docx.oxml.ns',
        'sqlite3',
        'sklearn',
        'sklearn.metrics.pairwise',
        'sklearn.feature_extraction.text',
        'src.literature.db_manager',
        'src.draft.analyzer',
        'src.citation.matcher',
        'src.citation.ai_matcher',
        'src.citation.search_engine',
        'src.citation.format_learner',
        'src.utils.config',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'PIL',
        'tkinter',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'sphinx',
        'sentence_transformers',
        'faiss',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='论文反插助手',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='论文反插助手'
)
"""
    spec_path.write_text(spec_content, encoding="utf-8")


def create_readme():
    readme = DIST_DIR / "论文反插助手" / "README.txt"
    readme.write_text(
        """论文反插助手 - 使用说明
========================

版本说明：
这是"无模型版"，不包含 AI 向量模型，使用传统关键词检索。

使用方法：
1. 双击"启动.bat"或"论文反插助手.exe"
2. 在浏览器中访问 http://localhost:8501
3. 使用侧边栏导入文献库并上传草稿

注意事项：
- 此版本使用传统关键词匹配，检索质量略低于完整版
- 如需使用 AI 混合检索，请使用在线版本或手动下载模型

数据保存：
- 文献库：data/literature.db
- 上传文件：uploads/
- 输出文件：output/

技术支持：
如有问题，请查看项目文档或联系开发者。
""",
        encoding="utf-8",
    )


def main():
    print("=" * 60)
    print("论文反插助手 - 无模型打包工具")
    print("=" * 60)
    print("\n说明: 此版本不包含 AI 模型，使用传统关键词检索")
    print("      文件体积更小，无需联网下载模型\n")

    check_pyinstaller()
    prepare_resources()
    clean_build()

    if build_exe():
        create_readme()

        print("\n" + "=" * 60)
        print("打包完成！")
        print("=" * 60)
        print(f"\n输出目录: {DIST_DIR / '论文反插助手'}")
        print("\n此版本特点:")
        print("  ✓ 文件体积小 (~150MB)")
        print("  ✓ 无需下载 AI 模型")
        print("  ✓ 开箱即用")
        print("  ⚠ 使用传统关键词检索（非 AI 检索）")
        print("=" * 60)
    else:
        print("\n✗ 打包失败")


if __name__ == "__main__":
    main()
