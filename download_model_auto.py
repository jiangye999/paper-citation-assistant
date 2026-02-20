#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载 HuggingFace 模型（自动检测并使用系统代理）
"""

import os
import sys
import socket
from pathlib import Path


# 尝试检测系统代理
def detect_proxy():
    """检测系统代理设置"""
    proxy_vars = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]

    for var in proxy_vars:
        if var in os.environ:
            return os.environ[var]

    # 尝试常见代理端口
    common_ports = [7890, 7897, 1080, 10808, 8080, 8118]
    for port in common_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(("127.0.0.1", port))
            sock.close()
            if result == 0:
                proxy_url = f"http://127.0.0.1:{port}"
                print(f"[OK] 检测到代理: {proxy_url}")
                return proxy_url
        except:
            pass

    return None


# 清除镜像站设置
os.environ.pop("HF_ENDPOINT", None)
os.environ.pop("HF_HUB_OFFLINE", None)
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# 设置代理
detected_proxy = detect_proxy()
if detected_proxy:
    os.environ["HTTP_PROXY"] = detected_proxy
    os.environ["HTTPS_PROXY"] = detected_proxy
    print(f"[OK] 使用代理: {detected_proxy}")
else:
    print("[WARN] 未检测到代理，尝试直连...")

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
        local_files_only=False,
    )

    print("\n" + "=" * 60)
    print("[OK] 模型下载成功！")
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
    print(f"[OK] 模型测试成功，向量维度: {len(test_embedding)}")

    print("\n" + "=" * 60)
    print("现在可以打包完整版 exe 了！")
    print("运行: python build.py")
    print("=" * 60)

except Exception as e:
    print(f"\n[ERROR] 下载失败: {e}")
    print("\n可能的原因:")
    print("1. VPN 未连接或未配置代理")
    print("2. 网络不稳定")
    print("3. 磁盘空间不足")
    print("\n解决方案:")
    print("1. 确认 VPN 已连接")
    print("2. 手动设置代理:")
    print("   set HTTP_PROXY=http://127.0.0.1:代理端口")
    print("   set HTTPS_PROXY=http://127.0.0.1:代理端口")
    print("3. 使用无模型版本: python build_no_model.py")
    sys.exit(1)
