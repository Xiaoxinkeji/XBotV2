"""
XBotV2配置工具模块
提供统一的配置文件读写功能，处理不同Python版本的TOML库兼容性
"""

import os
import logging
import traceback
from pathlib import Path

# 处理TOML库的兼容性
toml_parser = None
toml_writer = None

try:
    import tomli
    toml_parser = tomli
except ImportError:
    pass

try:
    import tomllib
    if not toml_parser:
        toml_parser = tomllib
except ImportError:
    pass

try:
    import toml
    toml_writer = toml
    if not toml_parser:
        toml_parser = toml
except ImportError:
    pass

logger = logging.getLogger("config_utils")

def load_toml_config(file_path):
    """
    读取TOML配置文件
    
    Args:
        file_path: 配置文件路径
        
    Returns:
        dict: 配置字典，如果读取失败则返回空字典
    """
    try:
        if not toml_parser:
            raise ImportError("未找到可用的TOML解析库，请安装tomli、tomllib或toml库")
        
        file_path = Path(file_path)
        if not file_path.exists():
            logger.error(f"配置文件不存在: {file_path}")
            return {}
        
        # tomli和tomllib需要二进制模式读取
        if toml_parser.__name__ in ['tomli', 'tomllib']:
            with open(file_path, "rb") as f:
                return toml_parser.load(f)
        else:
            # toml库使用文本模式
            with open(file_path, "r", encoding="utf-8") as f:
                return toml_parser.load(f)
    except Exception as e:
        logger.error(f"读取配置文件出错 ({file_path}): {e}")
        logger.error(traceback.format_exc())
        return {}

def save_toml_config(file_path, config_data):
    """
    保存TOML配置文件
    
    Args:
        file_path: 配置文件路径
        config_data: 要保存的配置数据
        
    Returns:
        bool: 保存是否成功
    """
    try:
        if not toml_writer:
            raise ImportError("未找到可用的TOML写入库，请安装toml库")
        
        file_path = Path(file_path)
        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            toml_writer.dump(config_data, f)
        return True
    except Exception as e:
        logger.error(f"保存配置文件出错 ({file_path}): {e}")
        logger.error(traceback.format_exc())
        return False 