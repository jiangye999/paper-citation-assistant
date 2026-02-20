#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从其他来源获取 HuggingFace 模型
"""

import os
import sys
import urllib.request
import json
from pathlib import Path


def download_from_modelscope():
    """
    从 ModelScope（魔搭社区）下载模型
    ModelScope 是国内平台，无需翻墙
    """
    print("尝试从 ModelScope 下载模型...")
    print("=" * 60)

    model_dir = Path(__file__).parent / "models" / "all-MiniLM-L6-v2"
    model_dir.mkdir(parents=True, exist_ok=True)

    # ModelScope 模型文件列表
    base_url = "https://www.modelscope.cn/models/iic/nlp_corom_sentence-embedding_english-base/resolve/master"

    # 需要下载的文件（根据sentence-transformers格式）
    files_to_download = [
        ("config.json", "config.json"),
        ("pytorch_model.bin", "pytorch_model.bin"),
        ("tokenizer_config.json", "tokenizer_config.json"),
        ("vocab.txt", "vocab.txt"),
        ("special_tokens_map.json", "special_tokens_map.json"),
        ("tokenizer.json", "tokenizer.json"),
    ]

    print("注意: ModelScope上可能没有完全匹配的模型")
    print("如果下载失败，请使用其他方式获取模型\n")

    success_count = 0
    for remote_name, local_name in files_to_download:
        url = f"{base_url}/{remote_name}"
        local_path = model_dir / local_name

        try:
            print(f"下载: {local_name} ...", end=" ")
            urllib.request.urlretrieve(url, str(local_path))
            print("✓")
            success_count += 1
        except Exception as e:
            print(f"✗ ({e})")

    if success_count > 0:
        print(f"\n✓ 下载了 {success_count} 个文件")
        print(f"位置: {model_dir}")
        return True
    else:
        print("\n✗ 下载失败")
        return False


def create_model_from_cache():
    """
    如果你有其他项目已经下载了这个模型，可以从此处复制
    """
    print("\n" + "=" * 60)
    print("手动迁移模型")
    print("=" * 60)
    print("\n如果你有其他Python项目已经下载了all-MiniLM-L6-v2模型:")
    print()
    print("1. 在文件资源管理器中搜索 'sentence-transformers'")
    print("2. 找到 all-MiniLM-L6-v2 文件夹")
    print("3. 复制整个文件夹到本项目的 models/ 目录")
    print()
    print("目标路径:")
    print(f"   {Path(__file__).parent / 'models' / 'all-MiniLM-L6-v2'}")
    print()
    print("或者运行:")
    print("   python migrate_model.py <模型路径>")


def main():
    print("=" * 60)
    print("HuggingFace 模型下载工具")
    print("=" * 60)
    print()
    print("搜索了以下位置，未找到已下载的模型:")
    print("  - C:\\Users\\Administrator\\.cache\\torch\\sentence_transformers")
    print("  - C:\\Users\\Administrator\\.cache\\huggingface\\hub")
    print()

    # 尝试从 ModelScope 下载
    if download_from_modelscope():
        return

    # 提供手动方案
    create_model_from_cache()

    print("\n" + "=" * 60)
    print("备选方案: 无模型打包")
    print("=" * 60)
    print()
    print("如果无法获取模型，可以打包无模型版本:")
    print("  python build_no_model.py")
    print()
    print("无模型版本特点:")
    print("  ✓ 文件体积小 (~150MB)")
    print("  ✓ 无需联网下载")
    print("  ⚠ 使用传统关键词检索（非AI向量检索）")
    print("  ⚠ 检索质量略低，但功能完整")


if __name__ == "__main__":
    main()
