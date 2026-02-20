#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查找并迁移 HuggingFace 模型到项目目录
"""

import os
import sys
import shutil
from pathlib import Path


def find_model():
    """查找已下载的 all-MiniLM-L6-v2 模型"""

    print("正在搜索已下载的 HuggingFace 模型...")
    print("=" * 60)

    # 可能的缓存路径
    possible_paths = [
        # Windows 默认缓存路径
        Path.home() / ".cache" / "torch" / "sentence_transformers",
        Path.home() / ".cache" / "huggingface" / "hub",
        Path.home() / ".cache" / "huggingface" / "transformers",
        # 其他可能路径
        Path.home() / ".torch" / "sentence_transformers",
        Path("C:/Users/Administrator/.cache/torch/sentence_transformers"),
        Path("C:/Users/Administrator/.cache/huggingface/hub"),
        # 项目目录
        Path(__file__).parent / "models",
        # 当前工作目录
        Path.cwd() / "models",
    ]

    model_name_keywords = ["MiniLM", "sentence-transformers", "all-MiniLM-L6-v2"]
    found_models = []

    for base_path in possible_paths:
        if not base_path.exists():
            continue

        print(f"\n搜索路径: {base_path}")

        try:
            # 遍历目录
            for item in base_path.rglob("*"):
                if item.is_dir():
                    dir_name = str(item).lower()
                    # 检查是否包含模型关键词
                    if any(
                        keyword.lower() in dir_name for keyword in model_name_keywords
                    ):
                        # 检查是否包含模型文件
                        if (item / "config.json").exists() or (
                            item / "pytorch_model.bin"
                        ).exists():
                            found_models.append(item)
                            print(f"  ✓ 找到模型: {item}")
                            print(f"    大小: {get_folder_size(item):.1f} MB")
        except PermissionError:
            print(f"  ✗ 无法访问该路径")
        except Exception as e:
            print(f"  ✗ 搜索出错: {e}")

    return found_models


def get_folder_size(path):
    """获取文件夹大小（MB）"""
    total = 0
    for file in path.rglob("*"):
        if file.is_file():
            total += file.stat().st_size
    return total / (1024 * 1024)


def migrate_model(source_path, target_path):
    """迁移模型到项目目录"""

    print(f"\n{'=' * 60}")
    print(f"正在迁移模型...")
    print(f"从: {source_path}")
    print(f"到: {target_path}")
    print(f"{'=' * 60}")

    try:
        # 创建目标目录
        target_path.mkdir(parents=True, exist_ok=True)

        # 复制文件
        print("正在复制文件...")
        for item in source_path.rglob("*"):
            if item.is_file():
                relative_path = item.relative_to(source_path)
                dest_file = target_path / relative_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest_file)
                print(f"  ✓ {relative_path}")

        print(f"\n✓ 模型迁移完成！")
        print(f"  目标位置: {target_path}")
        print(f"  大小: {get_folder_size(target_path):.1f} MB")
        return True

    except Exception as e:
        print(f"✗ 迁移失败: {e}")
        return False


def main():
    print("HuggingFace 模型迁移工具")
    print("=" * 60)

    # 查找模型
    models = find_model()

    if not models:
        print("\n" + "=" * 60)
        print("未找到已下载的模型")
        print("=" * 60)
        print("\n可能的原因:")
        print("1. 模型尚未下载")
        print("2. 模型下载到了其他位置")
        print("\n解决方案:")
        print("1. 先运行一次应用，让模型自动下载")
        print("2. 手动指定模型路径:")
        print(f"   python migrate_model.py <模型路径>")
        return

    # 显示找到的模型
    print(f"\n{'=' * 60}")
    print(f"找到 {len(models)} 个模型")
    print(f"{'=' * 60}")

    for i, model_path in enumerate(models, 1):
        print(f"\n[{i}] {model_path}")
        print(f"    大小: {get_folder_size(model_path):.1f} MB")

    # 选择要迁移的模型
    if len(models) == 1:
        selected = models[0]
        print(f"\n自动选择唯一的模型")
    else:
        print(f"\n请选择要迁移的模型 (1-{len(models)}): ", end="")
        try:
            choice = int(input()) - 1
            if 0 <= choice < len(models):
                selected = models[choice]
            else:
                print("无效选择")
                return
        except ValueError:
            print("请输入数字")
            return

    # 迁移模型
    project_root = Path(__file__).parent
    target = project_root / "models" / "all-MiniLM-L6-v2"

    if migrate_model(selected, target):
        print(f"\n{'=' * 60}")
        print("✓ 模型迁移成功！")
        print(f"{'=' * 60}")
        print(f"\n现在可以打包 exe 了:")
        print(f"  python build.py")
    else:
        print(f"\n✗ 迁移失败")


if __name__ == "__main__":
    # 支持命令行参数
    if len(sys.argv) > 1:
        source = Path(sys.argv[1])
        if source.exists():
            target = Path(__file__).parent / "models" / "all-MiniLM-L6-v2"
            migrate_model(source, target)
        else:
            print(f"路径不存在: {source}")
    else:
        main()
