#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载 HuggingFace 模型（使用VPN直连）
"""

import os
import sys
from pathlib import Path

# 清除镜像站设置，使用官方源
os.environ.pop("HF_ENDPOINT", None)
os.environ.pop("HF_HUB_OFFLINE", None)
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# 设置本地缓存目录
project_root = Path(__file__).parent
model_cache = project_root / "models"
model_cache.mkdir(exist_ok=True)

print("=" * 60)
print("下载 HuggingFace 模型")
print("=" * 60)
print(f"\n目标目录: {model_cache}")
print("下载源: https://huggingface.co (官方)")
print("模型: sentence-transformers/all-MiniLM-L6-v2")
print()

try:
    from sentence_transformers import SentenceTransformer

    print("开始下载... (约100MB，可能需要几分钟)")
    print("-" * 60)

    # 下载模型到项目目录
    model = SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2",
        cache_folder=str(model_cache),
        local_files_only=False,  # 强制从网络下载
    )

    print("\n" + "=" * 60)
    print("✓ 模型下载成功！")
    print("=" * 60)

    # 显示下载的模型信息
    print(f"\n模型路径: {model_cache}")

    # 列出下载的文件
    model_files = list(model_cache.rglob("*"))
    print(f"\n下载了 {len(model_files)} 个文件/目录")

    # 计算大小
    total_size = 0
    for f in model_files:
        if f.is_file():
            total_size += f.stat().st_size
    print(f"总大小: {total_size / 1024 / 1024:.1f} MB")

    # 测试模型
    print("\n测试模型...")
    test_embedding = model.encode("This is a test sentence.")
    print(f"✓ 模型测试成功，向量维度: {len(test_embedding)}")

    print("\n" + "=" * 60)
    print("现在可以打包完整版 exe 了！")
    print("运行: python build.py")
    print("=" * 60)

except Exception as e:
    print(f"\n✗ 下载失败: {e}")
    print("\n可能的原因:")
    print("1. VPN 未生效 - 请确认VPN已连接")
    print("2. 网络不稳定 - 请重试")
    print("3. 磁盘空间不足 - 需要至少 150MB")
    print("\n备选方案:")
    print("  python build_no_model.py  (无模型版本)")
    sys.exit(1)
