#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论文反插助手 - 低配置打包脚本
针对内存不足 (8GB 或以下) 和低网速环境优化

主要优化：
1. 跳过模型下载（使用在线加载或手动下载）
2. 分阶段打包，减少内存峰值
3. 使用 --onedir 模式，更快更稳定
4. 可选：创建精简版（不含模型，体积更小）
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


def print_step(step, total, message):
    """打印步骤信息"""
    print(f"\n{'=' * 60}")
    print(f"[{step}/{total}] {message}")
    print(f"{'=' * 60}")


def check_pyinstaller():
    """检查 PyInstaller"""
    try:
        import PyInstaller

        version = PyInstaller.__version__
        print(f"✓ PyInstaller 已安装 (版本：{version})")
        return True
    except ImportError:
        print("⚠ PyInstaller 未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller", "-q"])
        print("✓ PyInstaller 安装完成")
        return True


def check_models():
    """检查模型文件"""
    print("\n检查模型文件...")

    model1 = MODELS_DIR / "all-MiniLM-L6-v2"
    model2 = MODELS_DIR / "cross-encoder_ms-marco-MiniLM-L-6-v2"

    has_model1 = model1.exists() and any(model1.iterdir())
    has_model2 = model2.exists() and any(model2.iterdir())

    if has_model1:
        print(f"  ✓ 向量模型已存在：{model1.name}")
    else:
        print(f"  ✗ 向量模型不存在：{model1.name}")

    if has_model2:
        print(f"  ✓ Cross-encoder 模型已存在：{model2.name}")
    else:
        print(f"  ✗ Cross-encoder 模型不存在：{model2.name}")

    return has_model1, has_model2


def manual_model_download():
    """手动下载模型指导"""
    print("\n" + "=" * 60)
    print("模型下载指南（如果自动下载失败）")
    print("=" * 60)
    print("""
方法 1: 使用 Hugging Face 镜像（推荐）
-----------------------------------
打开浏览器访问：
https://hf-mirror.com/sentence-transformers/all-MiniLM-L6-v2

下载后解压到：models/all-MiniLM-L6-v2/

方法 2: 使用 Python 脚本下载
-----------------------------------
在命令行运行：
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2', cache_folder='models')"

如果下载慢，先设置镜像：
set HF_ENDPOINT=https://hf-mirror.com
然后再运行上面的命令

方法 3: 跳过模型（推荐低配置用户）
-----------------------------------
打包时不包含模型，用户首次使用时自动下载
或手动复制模型文件到 models/ 目录
""")


def create_lite_spec():
    """创建精简版 spec 文件（不包含大模型）"""
    spec_content = """# -*- mode: python ; coding: utf-8 -*-
# 精简版 spec - 不包含 AI 模型，适合低配置电脑
import os
from pathlib import Path

# 获取项目根目录
project_root = Path(r"E:\\AI_projects\\论文反插助手 - 副本")

# 数据文件（不包含模型）
data_files = [
    (str(project_root / 'config' / 'config.yaml'), 'config'),
    (str(project_root / 'data'), 'data'),
    (str(project_root / 'uploads'), 'uploads'),
    (str(project_root / 'output'), 'output'),
]

# 分析配置
a = Analysis(
    [str(project_root / 'app.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=data_files,
    hiddenimports=[
        # Streamlit 相关
        'streamlit',
        'streamlit.runtime.scriptrunner.script_runner',
        # 数据处理
        'pandas',
        'pandas._libs.tslibs.base',
        'numpy',
        # 文档处理
        'docx',
        'docx.oxml.ns',
        # 数据库
        'sqlite3',
        # 机器学习
        'sklearn',
        'sklearn.metrics.pairwise',
        'sklearn.feature_extraction.text',
        # 向量检索（库文件，不含模型）
        'sentence_transformers',
        'faiss',
        # 项目模块
        'src.literature.db_manager',
        'src.draft.analyzer',
        'src.citation.matcher',
        'src.citation.ai_matcher',
        'src.citation.search_engine',
        'src.citation.rag_retriever',
        'src.citation.vector_search',
        'src.citation.format_learner',
        'src.utils.config',
    ],
    excludes=[
        # 排除不必要的库以减小体积和内存占用
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
        # 排除大型库的可选组件
        'scipy.linalg',
        'scipy.sparse.csgraph',
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
    name='论文反插助手_lite',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # UPX 压缩（减小体积）
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='论文反插助手_lite'
)
"""

    spec_path = BUILD_DIR / "lite.spec"
    spec_path.parent.mkdir(exist_ok=True)
    spec_path.write_text(spec_content, encoding="utf-8")
    print(f"✓ 精简版 spec 已创建：{spec_path}")
    return spec_path


def build_lite():
    """构建精简版（不含模型）"""
    print_step(1, 3, "构建精简版（不含 AI 模型）")

    spec_path = create_lite_spec()

    # 清理缓存
    print("\n清理缓存...")
    for cache_dir in list(PROJECT_ROOT.rglob("__pycache__")):
        try:
            shutil.rmtree(cache_dir)
        except:
            pass

    # 构建命令（低内存优化）
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        str(spec_path),
        "--clean",  # 清理临时文件
        "--noconfirm",  # 不询问确认
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(BUILD_DIR / "lite_work"),
    ]

    print(f"\n开始构建...")
    print(f"命令：{' '.join(cmd)}")
    print(f"这将需要 3-8 分钟，请耐心等待...")
    print(f"\n提示：如果长时间无响应，可能是内存不足，请关闭其他程序")

    # 设置环境变量优化内存
    env = os.environ.copy()
    env["PYINSTALLER_DEBUG"] = "0"  # 减少调试信息

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)

    if result.returncode == 0:
        print("\n✓ 构建成功！")
        exe_path = DIST_DIR / "论文反插助手_lite" / "论文反插助手_lite.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / 1024 / 1024
            print(f"✓ 可执行文件：{exe_path.name}")
            print(f"✓ 文件大小：{size_mb:.1f} MB")
        return True
    else:
        print("\n✗ 构建失败")
        print(f"错误信息:\n{result.stderr[-1000:]}")
        return False


def create_launcher():
    """创建启动器"""
    print_step(2, 3, "创建启动器")

    launcher_dir = DIST_DIR / "论文反插助手_lite"
    launcher_dir.mkdir(exist_ok=True)

    launcher_bat = launcher_dir / "启动.bat"
    launcher_bat.write_text(
        """@echo off
chcp 65001 >nul
title 论文反插助手
echo ========================================
echo   论文反插助手 - 启动中...
echo ========================================
echo.
echo 正在启动，请稍候...
echo.
论文反插助手_lite.exe
pause
""",
        encoding="gbk",
    )
    print(f"✓ 启动器已创建：{launcher_bat}")

    # 创建使用说明
    readme = launcher_dir / "使用说明.txt"
    readme.write_text(
        """论文反插助手 - 使用说明
========================

启动方法：
1. 双击 "启动.bat" 或 "论文反插助手_lite.exe"
2. 浏览器会自动打开 http://localhost:8501
3. 如果未自动打开，手动访问上述地址

首次使用：
- 系统会自动下载 AI 模型（约 100MB）
- 请保持网络连接
- 下载可能需要几分钟

手动下载模型（推荐）：
如果自动下载失败，请手动下载模型：
1. 访问：https://hf-mirror.com/sentence-transformers/all-MiniLM-L6-v2
2. 下载后解压到本目录的 models/ 文件夹

注意事项：
- 数据保存在 data/ 目录
- 导出文件在 output/ 目录
- 首次启动需要 10-30 秒加载

技术支持：
如遇问题，请查看控制台错误信息
""",
        encoding="utf-8",
    )
    print(f"✓ 使用说明已创建：{readme}")


def create_batch_file():
    """创建一键打包批处理文件"""
    print_step(3, 3, "创建批处理文件")

    batch_file = PROJECT_ROOT / "一键打包_lite.bat"
    batch_file.write_text(
        """@echo off
chcp 65001 >nul
title 论文反插助手 - 打包工具

echo ========================================
echo   论文反插助手 - 低配置打包工具
echo ========================================
echo.
echo 此脚本将创建精简版安装包（不含 AI 模型）
echo 优点：打包快、内存占用低、体积小
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
echo 输出目录：dist\\论文反插助手_lite
echo.
pause
""",
        encoding="gbk",
    )
    print(f"✓ 批处理文件已创建：{batch_file}")


def main():
    """主函数"""
    print("=" * 60)
    print("论文反插助手 - 低配置打包工具")
    print("=" * 60)
    print("\n此模式适合：")
    print("  - 内存 ≤ 8GB 的电脑")
    print("  - 网络速度慢的环境")
    print("  - 之前标准版打包失败的用户")
    print("\n特点：")
    print("  - 不包含 AI 模型（减小 200MB+）")
    print("  - 内存占用更低")
    print("  - 打包速度更快")
    print("  - 用户首次使用时自动下载模型")

    # 检查 PyInstaller
    print_step(0, 3, "检查环境")
    check_pyinstaller()

    # 检查模型
    has_model1, has_model2 = check_models()
    if not has_model1:
        print("\n⚠ 未检测到模型文件")
        print("  精简版将不包含模型，用户需自行下载")
        manual_model_download()

    # 确认开始
    print("\n" + "=" * 60)
    response = input("是否继续打包？(y/n): ").strip().lower()
    if response != "y":
        print("已取消")
        return

    # 开始构建
    if build_lite():
        create_launcher()
        create_batch_file()

        print("\n" + "=" * 60)
        print("🎉 打包完成！")
        print("=" * 60)
        print(f"\n输出目录：{DIST_DIR / '论文反插助手_lite'}")
        print("\n下一步：")
        print("  1. 测试：运行 '论文反插助手_lite.exe' 确认能启动")
        print("  2. 分发：压缩整个文件夹为用户版")
        print("  3. 模型：告知用户下载模型或手动放入 models/ 目录")
        print("\n" + "=" * 60)
    else:
        print("\n" + "=" * 60)
        print("✗ 打包失败")
        print("=" * 60)
        print("\n建议：")
        print("  1. 关闭其他程序，释放内存")
        print("  2. 重启电脑后重试")
        print("  3. 检查 Python 版本（推荐 3.8-3.10）")
        print("  4. 查看详细错误信息 above")


if __name__ == "__main__":
    main()
