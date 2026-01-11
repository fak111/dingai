#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI 启动入口 - 用于打包
这个文件只做最少的初始化，然后启动 GUI
"""

import sys
import os

# 确保能找到打包后的模块
if getattr(sys, "frozen", False):
    # 打包后的路径
    base_path = sys._MEIPASS
    # 添加数据文件路径到 sys.path
    data_path = os.path.dirname(sys.executable)
    if data_path not in sys.path:
        sys.path.insert(0, data_path)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

# 导入并运行 GUI
import gui

gui.start_gui()
