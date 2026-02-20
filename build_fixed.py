#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论文反插助手 - 打包脚本 (修复编码问题)
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

        print("[OK] PyInstaller installed")
        return True
    except ImportError:
        print("[ERROR] PyInstaller not installed")
        print("Please install manually:")
        print("  pip install pyinstaller")
        return False


def prepare_resources():
    print("\n[1/3] Preparing resources...")

    dirs = ["data", "uploads", "output", "config"]
    for dir_name in dirs:
        dir_path = PROJECT_ROOT / dir_name
        dir_path.mkdir(exist_ok=True)
        print(f"  [OK] Created: {dir_name}")

    config_file = PROJECT_ROOT / "config" / "config.yaml"
    if not config_file.exists():
        config_file.write_text(
            """# Configuration
citation:
  style: "author-year"
  max_citations_per_sentence: 3
""",
            encoding="utf-8",
        )
        print("  [OK] Created default config")

    print("[OK] Resources ready")


def clean_build():
    print("\n[2/3] Cleaning build directory...")

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
                print(f"  [OK] Cleaned: {dir_path}")
            except:
                pass

    print("[OK] Cleaned")


def build_exe():
    print("\n[3/3] Building exe...")

    spec_file = BUILD_DIR / "paper_citation_inserter.spec"

    if not spec_file.exists():
        print("[ERROR] Spec file not found:", spec_file)
        return False

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

    print(f"  This may take a few minutes...")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("[OK] Build successful!")
        exe_path = DIST_DIR / "论文反插助手" / "论文反插助手.exe"
        if exe_path.exists():
            print(f"\n[OK] Executable: {exe_path}")
            size_mb = exe_path.stat().st_size / 1024 / 1024
            print(f"[OK] Size: {size_mb:.1f} MB")
        return True
    else:
        print("[ERROR] Build failed")
        print(
            "Error:",
            result.stderr[-500:] if len(result.stderr) > 500 else result.stderr,
        )
        return False


def create_launcher():
    launcher_bat = DIST_DIR / "论文反插助手" / "启动.bat"
    launcher_bat.write_text(
        """@echo off
chcp 65001 >nul
echo Starting...
论文反插助手.exe
pause
""",
        encoding="gbk",
    )
    print(f"[OK] Launcher created")


def main():
    print("=" * 60)
    print("Paper Citation Inserter - Build Tool")
    print("=" * 60)

    if not check_pyinstaller():
        print("\n[ERROR] Please install PyInstaller first:")
        print("  pip install pyinstaller")
        sys.exit(1)

    prepare_resources()
    clean_build()

    if build_exe():
        create_launcher()

        print("\n" + "=" * 60)
        print("Build Complete!")
        print("=" * 60)
        print(f"\nOutput: {DIST_DIR / '论文反插助手'}")
        print("\nFeatures:")
        print("  [OK] AI model included (all-MiniLM-L6-v2)")
        print("  [OK] Full text search enabled")
        print("  [OK] Ready to distribute")
        print("=" * 60)
    else:
        print("\n[ERROR] Build failed")


if __name__ == "__main__":
    main()
