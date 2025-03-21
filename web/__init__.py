"""
XBotV2 Web管理界面模块
"""

import sys
import os
import threading
import tomllib
from pathlib import Path

from loguru import logger

# 确保可以导入主项目模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def start_web_server():
    """启动Web服务器的入口函数"""
    from web.app import start_web_server as start
    start() 