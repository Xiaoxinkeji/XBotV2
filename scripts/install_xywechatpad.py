#!/usr/bin/env python3
"""
专门用于安装xywechatpad-binary的脚本
"""
import sys
import os
import subprocess
import logging
import platform
import tempfile

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("install_xywechatpad")

def get_system_info():
    """获取系统信息"""
    return {
        "system": platform.system(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
        "platform": platform.platform()
    }

def install_with_pip(version="1.1.0", index_url=None):
    """使用pip安装"""
    try:
        cmd = [sys.executable, "-m", "pip", "install", f"xywechatpad-binary=={version}"]
        
        if index_url:
            cmd.extend(["--index-url", index_url])
            
        logger.info(f"尝试使用pip安装xywechatpad-binary=={version}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("安装成功!")
            return True
        else:
            logger.warning(f"安装失败: {result.stderr.strip()}")
            return False
    except Exception as e:
        logger.error(f"安装过程出错: {str(e)}")
        return False

def install_from_wheel(wheel_path):
    """从wheel文件安装"""
    try:
        logger.info(f"尝试从wheel安装: {wheel_path}")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", wheel_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("安装成功!")
            return True
        else:
            logger.warning(f"安装失败: {result.stderr.strip()}")
            return False
    except Exception as e:
        logger.error(f"安装过程出错: {str(e)}")
        return False

def find_wheel_files():
    """查找可能的wheel文件"""
    wheel_files = []
    
    # 检查常见目录
    for directory in ["wheels", "dist", "downloads", "."]:
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                if filename.startswith("xywechatpad") and filename.endswith(".whl"):
                    wheel_files.append(os.path.join(directory, filename))
    
    return wheel_files

def main():
    """主函数"""
    system_info = get_system_info()
    logger.info(f"系统信息: {system_info}")
    
    # 1. 尝试从PyPI安装
    if install_with_pip():
        return 0
        
    # 2. 尝试从其他镜像安装
    mirrors = [
        "https://mirrors.aliyun.com/pypi/simple/",
        "https://pypi.tuna.tsinghua.edu.cn/simple/",
        "https://pypi.doubanio.com/simple/"
    ]
    
    for mirror in mirrors:
        logger.info(f"尝试从镜像安装: {mirror}")
        if install_with_pip(index_url=mirror):
            return 0
    
    # 3. 尝试从wheel文件安装
    wheel_files = find_wheel_files()
    if wheel_files:
        logger.info(f"找到 {len(wheel_files)} 个可能的wheel文件")
        for wheel_file in wheel_files:
            if install_from_wheel(wheel_file):
                return 0
    
    # 4. 尝试从源码安装
    if os.path.exists("xywechatpad-binary"):
        logger.info("尝试从源码安装")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", "xywechatpad-binary"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("从源码安装成功!")
            return 0
    
    logger.error("所有安装方法均失败")
    return 1

if __name__ == "__main__":
    sys.exit(main()) 