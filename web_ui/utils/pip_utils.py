"""
PIP 工具函数，处理依赖安装
"""
import os
import subprocess
import logging
import sys
from typing import List, Optional

logger = logging.getLogger(__name__)

def install_package(package_name: str, version: Optional[str] = None, index_url: Optional[str] = None) -> bool:
    """
    安装指定的包
    
    :param package_name: 包名
    :param version: 版本号(可选)
    :param index_url: 自定义索引URL(可选)
    :return: 是否安装成功
    """
    try:
        package_spec = f"{package_name}=={version}" if version else package_name
        cmd = [sys.executable, "-m", "pip", "install", package_spec]
        
        if index_url:
            cmd.extend(["--index-url", index_url])
            
        logger.info(f"正在安装包: {package_spec}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"成功安装包: {package_spec}")
            return True
        else:
            logger.error(f"安装包失败: {package_spec}")
            logger.error(f"错误信息: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"安装包时出错: {str(e)}")
        return False

def find_wheel_file(package_name: str, directory: str = "wheels") -> Optional[str]:
    """
    在指定目录中查找wheel文件
    
    :param package_name: 包名
    :param directory: 查找目录
    :return: wheel文件路径或None
    """
    if not os.path.exists(directory):
        return None
        
    for filename in os.listdir(directory):
        if filename.startswith(package_name) and filename.endswith(".whl"):
            return os.path.join(directory, filename)
            
    return None

def install_from_wheel(wheel_path: str) -> bool:
    """
    从wheel文件安装包
    
    :param wheel_path: wheel文件路径
    :return: 是否安装成功
    """
    try:
        logger.info(f"正在从wheel安装: {wheel_path}")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", wheel_path],
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            logger.info(f"成功从wheel安装: {wheel_path}")
            return True
        else:
            logger.error(f"从wheel安装失败: {wheel_path}")
            logger.error(f"错误信息: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"从wheel安装时出错: {str(e)}")
        return False

def install_special_package(package_name: str, version: str) -> bool:
    """
    尝试多种方式安装特殊包
    
    :param package_name: 包名
    :param version: 版本号
    :return: 是否安装成功
    """
    # 1. 首先尝试从默认PyPI安装
    if install_package(package_name, version):
        return True
        
    # 2. 尝试从项目的wheels目录安装
    wheel_path = find_wheel_file(package_name)
    if wheel_path and install_from_wheel(wheel_path):
        return True
        
    # 3. 尝试从源码安装
    if os.path.exists(package_name):
        logger.info(f"尝试从源码安装: {package_name}")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", package_name],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return True
    
    # 4. 尝试从私有index安装
    private_indexes = [
        "http://localhost:8080/simple/",  # 本地PyPI服务器
        "http://pypi.internal/simple/",   # 内部PyPI服务器
    ]
    
    for index in private_indexes:
        if install_package(package_name, version, index_url=index):
            return True
    
    return False 