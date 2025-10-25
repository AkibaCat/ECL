#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动脚本 - 程序的入口点
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(__file__))

from main import MinecraftLauncher

if __name__ == "__main__":
    # 检查依赖
    try:
        import tkinter
        import requests
    except ImportError as e:
        print(f"缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        sys.exit(1)
    
    # 启动启动器
    launcher = MinecraftLauncher()
    launcher.run()