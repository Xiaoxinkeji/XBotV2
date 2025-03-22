"""
XBotV2 Web管理界面模块
"""

import sys
import os
import threading
# 处理TOML库的兼容性
try:
    import tomli as toml_parser  # Python 3.11前
except ImportError:
    try:
        import tomllib as toml_parser  # Python 3.11+
    except ImportError:
        import toml as toml_parser  # 回退到toml库
from pathlib import Path

from loguru import logger

# 确保可以导入主项目模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def start_web_server():
    """启动Web服务器的入口函数"""
    from web.app import start_web_server as start
    start() 