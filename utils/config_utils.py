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
            logger.error("未找到可用的TOML解析库")
            # 尝试直接安装toml库
            try:
                import subprocess
                logger.info("尝试安装TOML库...")
                subprocess.check_call(["pip", "install", "toml"])
                import toml
                global toml_parser, toml_writer
                toml_parser = toml
                toml_writer = toml
                logger.info("成功安装并导入TOML库")
            except Exception as install_error:
                logger.error(f"安装TOML库失败: {install_error}")
                # 返回硬编码的基本配置以确保系统可用
                return {
                    "WebInterface": {
                        "username": "admin",
                        "password": "admin123"
                    }
                }
        
        file_path = Path(file_path)
        if not file_path.exists():
            logger.error(f"配置文件不存在: {file_path}")
            return {}
        
        file_content = None
        
        # 读取文件内容的备份，便于错误处理
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()
                logger.debug(f"配置文件大小: {len(file_content)} 字节")
        except Exception as read_error:
            logger.error(f"读取文件内容失败: {read_error}")
        
        # 尝试使用不同的TOML解析库解析
        if toml_parser.__name__ in ['tomli', 'tomllib']:
            try:
                with open(file_path, "rb") as f:
                    config = toml_parser.load(f)
                    logger.info(f"使用 {toml_parser.__name__} 解析TOML成功")
                    return config
            except Exception as binary_error:
                logger.error(f"使用 {toml_parser.__name__} 解析失败: {binary_error}")
                # 如果二进制模式失败，尝试使用文本模式
                if file_content and toml_writer:
                    try:
                        config = toml_writer.loads(file_content)
                        logger.info(f"使用 {toml_writer.__name__} 文本模式解析TOML成功")
                        return config
                    except Exception as text_error:
                        logger.error(f"使用文本模式解析也失败: {text_error}")
        else:
            # toml库使用文本模式
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    config = toml_parser.load(f)
                    logger.info(f"使用 {toml_parser.__name__} 解析TOML成功")
                    return config
            except Exception as text_error:
                logger.error(f"使用 {toml_parser.__name__} 解析失败: {text_error}")
                # 尝试手动解析基本的TOML格式
                if file_content:
                    try:
                        manual_config = manual_parse_toml(file_content)
                        if manual_config:
                            logger.info("使用手动解析TOML成功")
                            return manual_config
                    except Exception as manual_error:
                        logger.error(f"手动解析TOML失败: {manual_error}")
        
        # 所有方法都失败，返回硬编码的默认配置
        logger.warning("所有解析方法都失败，返回默认配置")
        return {
            "WebInterface": {
                "username": "admin",
                "password": "admin123"
            }
        }
    except Exception as e:
        logger.error(f"读取配置文件出错 ({file_path}): {e}")
        logger.error(traceback.format_exc())
        # 返回硬编码的默认配置
        return {
            "WebInterface": {
                "username": "admin",
                "password": "admin123"
            }
        }

def manual_parse_toml(content):
    """
    手动解析简单的TOML格式，作为最后的备选方案
    """
    config = {}
    current_section = ""
    
    for line in content.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
            
        # 处理部分头
        if line.startswith("[") and line.endswith("]"):
            current_section = line[1:-1].strip()
            config[current_section] = {}
        # 处理键值对
        elif "=" in line and current_section:
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            
            # 处理字符串值
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            # 处理数字
            elif value.isdigit():
                value = int(value)
            # 处理布尔值
            elif value.lower() in ["true", "false"]:
                value = value.lower() == "true"
                
            config[current_section][key] = value
            
    return config

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