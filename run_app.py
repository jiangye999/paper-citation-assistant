#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论文反插助手 - 打包启动器
用于将 Streamlit 应用打包成 exe
"""

import sys
import subprocess
import os
from pathlib import Path


def get_resource_path(relative_path):
    """获取资源文件的绝对路径"""
    if hasattr(sys, "_MEIPASS"):
        # PyInstaller 打包后的路径
        base_path = sys._MEIPASS
    else:
        # 开发环境路径
        base_path = Path(__file__).parent
    return base_path / relative_path


def main():
    if hasattr(sys, "_MEIPASS"):
        base_dir = Path(sys._MEIPASS)
    else:
        base_dir = Path(__file__).parent

    app_path = base_dir / "app.py"
    src_path = base_dir / "src"
    config_path = base_dir / "config"

    if not app_path.exists():
        print(f"错误: 找不到 app.py")
        print(f"搜索路径: {app_path}")
        print(f"目录内容: {list(base_dir.iterdir())}")
        input("按回车键退出...")
        sys.exit(1)

    os.chdir(base_dir)

    if src_path.exists():
        sys.path.insert(0, str(src_path))

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.port=8501",
        "--server.address=localhost",
        "--browser.gatherUsageStats=false",
    ]

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n已退出")
    except Exception as e:
        print(f"启动失败: {e}")
        input("按回车键退出...")
        sys.exit(1)

    # 切换到 exe 所在目录
    os.chdir(Path(sys.executable).parent)

    # 添加 src 目录到路径
    src_path = Path(sys.executable).parent / "src"
    if src_path.exists():
        sys.path.insert(0, str(src_path))

    # 启动 Streamlit
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.port=8501",
        "--server.address=localhost",
        "--browser.gatherUsageStats=false",
    ]

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n已退出")
    except Exception as e:
        print(f"启动失败: {e}")
        input("按回车键退出...")


if __name__ == "__main__":
    main()
