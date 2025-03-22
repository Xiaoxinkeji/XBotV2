"""
XBotV2配置工具模块
提供统一的配置文件读写功能，处理不同Python版本的TOML库兼容性
"""

import os
import logging
import traceback
from pathlib import Path

# 确保日志系统被正确初始化
try:
    from loguru import logger
except ImportError:
    # 如果没有loguru，使用标准logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("config_utils")

# 处理TOML库的兼容性
toml_parser = None
toml_writer = None

try:
    import tomli
    toml_parser = tomli
    logger.debug("成功导入tomli库")
except ImportError:
    logger.debug("导入tomli库失败")
    pass

try:
    import tomllib
    if not toml_parser:
        toml_parser = tomllib
        logger.debug("成功导入tomllib库")
except ImportError:
    logger.debug("导入tomllib库失败")
    pass

try:
    import toml
    toml_writer = toml
    if not toml_parser:
        toml_parser = toml
        logger.debug("成功导入toml库")
except ImportError:
    logger.debug("导入toml库失败")
    pass

# 确保至少有日志记录
if isinstance(logger, logging.Logger):
    logger = logging.getLogger("config_utils")

def load_toml_config(file_path):
    """
    读取TOML配置文件
    
    Args:
        file_path: 配置文件路径
        
    Returns:
        dict: 配置字典，如果读取失败则返回空字典
    """
    global toml_parser, toml_writer
    
    # 默认配置，确保系统在任何情况下都可用
    default_config = {
        "WebInterface": {
            "username": "admin",
            "password": "admin123",
            "enable": True,
            "host": "0.0.0.0",
            "port": 8080,
            "debug": False
        },
        "XYBot": {
            "version": "v1.0.0",
            "ignore-protection": False,
            "auto-restart": False
        },
        "WechatAPIServer": {
            "port": 9000,
            "mode": "release"
        }
    }
    
    try:
        # 如果参数无效，直接返回默认配置
        if not file_path:
            logger.error("配置文件路径为空")
            return default_config
            
        if not toml_parser:
            logger.error("未找到可用的TOML解析库")
            # 尝试直接安装toml库
            try:
                import subprocess
                logger.info("尝试安装TOML库...")
                subprocess.check_call(["pip", "install", "toml"])
                import toml
                toml_parser = toml
                toml_writer = toml
                logger.info("成功安装并导入TOML库")
            except Exception as install_error:
                logger.error(f"安装TOML库失败: {install_error}")
                return default_config
        
        # 确保file_path是Path对象
        try:
            file_path = Path(file_path)
        except Exception as path_error:
            logger.error(f"创建Path对象失败: {path_error}")
            return default_config
            
        if not file_path.exists():
            logger.error(f"配置文件不存在: {file_path}")
            # 尝试创建默认配置文件
            try:
                if toml_writer:
                    logger.info(f"创建默认配置文件: {file_path}")
                    save_toml_config(file_path, default_config)
                    return default_config
            except Exception as create_error:
                logger.error(f"创建默认配置文件失败: {create_error}")
            return default_config
        
        file_content = None
        
        # 读取文件内容的备份，便于错误处理
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()
                logger.debug(f"配置文件大小: {len(file_content)} 字节")
        except Exception as read_error:
            logger.error(f"读取文件内容失败: {read_error}")
            try:
                # 尝试以二进制模式读取
                with open(file_path, "rb") as f:
                    file_content = f.read().decode('utf-8', errors='ignore')
                    logger.debug(f"以二进制模式读取配置文件，大小: {len(file_content)} 字节")
            except Exception as binary_read_error:
                logger.error(f"以二进制模式读取文件内容失败: {binary_read_error}")
        
        config = None
        errors = []
        
        # 尝试使用不同的TOML解析库解析
        if toml_parser and hasattr(toml_parser, '__name__'):
            if toml_parser.__name__ in ['tomli', 'tomllib']:
                try:
                    with open(file_path, "rb") as f:
                        config = toml_parser.load(f)
                        logger.info(f"使用 {toml_parser.__name__} 解析TOML成功")
                except Exception as binary_error:
                    errors.append(f"使用 {toml_parser.__name__} 解析失败: {binary_error}")
                    # 如果二进制模式失败，尝试使用文本模式
                    if file_content and toml_writer:
                        try:
                            config = toml_writer.loads(file_content)
                            logger.info(f"使用 {toml_writer.__name__} 文本模式解析TOML成功")
                        except Exception as text_error:
                            errors.append(f"使用文本模式解析也失败: {text_error}")
            else:
                # toml库使用文本模式
                try:
                    if hasattr(toml_parser, 'load'):
                        with open(file_path, "r", encoding="utf-8") as f:
                            config = toml_parser.load(f)
                            logger.info(f"使用 {toml_parser.__name__} 解析TOML成功")
                    elif file_content and hasattr(toml_parser, 'loads'):
                        config = toml_parser.loads(file_content)
                        logger.info(f"使用 {toml_parser.__name__} 文本模式解析TOML成功")
                except Exception as text_error:
                    errors.append(f"使用 {toml_parser.__name__} 解析失败: {text_error}")
        
        # 如果以上方法都失败，尝试手动解析
        if not config and file_content:
            try:
                manual_config = manual_parse_toml(file_content)
                if manual_config:
                    logger.info("使用手动解析TOML成功")
                    config = manual_config
            except Exception as manual_error:
                errors.append(f"手动解析TOML失败: {manual_error}")
        
        # 确保配置中包含关键部分
        if config:
            # 确保WebInterface部分存在
            if "WebInterface" not in config:
                logger.warning("配置缺少WebInterface部分，使用默认值")
                config["WebInterface"] = default_config["WebInterface"]
            else:
                # 确保认证信息存在
                if "username" not in config["WebInterface"] or "password" not in config["WebInterface"]:
                    logger.warning("配置缺少认证信息，使用默认值")
                    config["WebInterface"]["username"] = default_config["WebInterface"]["username"]
                    config["WebInterface"]["password"] = default_config["WebInterface"]["password"]
            
            return config
        
        # 所有方法都失败，记录错误信息并返回默认配置
        if errors:
            logger.error("所有解析方法都失败:\n" + "\n".join(errors))
        
        logger.warning("所有解析方法都失败，返回默认配置")
        return default_config
        
    except Exception as e:
        logger.error(f"读取配置文件出错 ({file_path}): {e}")
        logger.error(traceback.format_exc())
        # 返回硬编码的默认配置
        return default_config

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