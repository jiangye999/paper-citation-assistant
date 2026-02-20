#!/usr/bin/env python3
"""
轻量版启动脚本
不包含AI模型，仅使用传统检索
"""

import sys
from pathlib import Path

# 禁用混合检索
sys.path.insert(0, str(Path(__file__).parent))

import os

os.environ["USE_HYBRID_SEARCH"] = "0"

# 启动streamlit
import subprocess

subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
