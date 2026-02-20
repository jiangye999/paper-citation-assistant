#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论文反插助手 - 打包启动器
用于将 Streamlit 应用打包成 exe
"""

import sys
import subprocess
import os
import time
from pathlib import Path


def main():
    # 确定运行目录
    if hasattr(sys, "_MEIPASS"):
        # PyInstaller 打包后的环境
        base_dir = Path(sys._MEIPASS)
        print(f"运行在打包环境中，资源目录：{base_dir}")
    else:
        # 开发环境
        base_dir = Path(__file__).parent
        print(f"运行在开发环境中，目录：{base_dir}")

    # 验证必要文件
    app_path = base_dir / "app.py"
    if not app_path.exists():
        print(f"❌ 错误：找不到 app.py")
        print(f"搜索路径：{app_path}")
        print(f"目录内容：{list(base_dir.iterdir())}")
        input("按回车键退出...")
        sys.exit(1)

    print(f"✅ 找到 app.py: {app_path}")

    # 添加 src 到路径
    src_path = base_dir / "src"
    if src_path.exists():
        sys.path.insert(0, str(src_path))
        print(f"✅ 添加 src 到路径：{src_path}")

    # 切换到资源目录
    os.chdir(base_dir)

    # 创建必要的目录
    for dir_name in ["data", "uploads", "output", "config"]:
        dir_path = base_dir / dir_name
        dir_path.mkdir(exist_ok=True)

    # 启动命令
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.port=8501",
        "--server.address=localhost",
        "--browser.gatherUsageStats=false",
        "--browser.serverAddress=localhost",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=true",
    ]

    print("\n" + "=" * 60)
    print("正在启动论文反插助手...")
    print("=" * 60)
    print(f"\n启动命令：{' '.join(cmd)}")
    print(f"\n应用将在浏览器中打开：http://localhost:8501")
    print("\n如果浏览器没有自动打开，请手动访问上述地址")
    print("\n按 Ctrl+C 停止服务...")
    print("=" * 60 + "\n")

    # 启动 Streamlit
    try:
        # 使用 Popen 而不是 run，以便更好地控制
        process = subprocess.Popen(cmd)

        # 等待进程结束
        process.wait()

    except KeyboardInterrupt:
        print("\n\n✅ 已停止服务")
    except Exception as e:
        print(f"\n❌ 启动失败：{e}")
        print(f"错误类型：{type(e).__name__}")
        import traceback

        traceback.print_exc()
        input("\n按回车键退出...")
        sys.exit(1)


if __name__ == "__main__":
    main()
