#!/usr/bin/env python3
"""
检查并恢复原始安装逻辑的脚本
"""
import os
import sys
import subprocess
import logging
import platform
import glob
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("restore_original")

def check_for_custom_wheels():
    """检查项目中是否有自定义wheels"""
    wheel_paths = []
    
    # 检查常见的wheel目录
    for wheel_dir in ["wheels", "dist", "vendor", "deps"]:
        if not os.path.exists(wheel_dir):
            continue
            
        for wheel_file in glob.glob(f"{wheel_dir}/*.whl"):
            wheel_paths.append(wheel_file)
    
    # 检查项目根目录
    for wheel_file in glob.glob("*.whl"):
        wheel_paths.append(wheel_file)
        
    return wheel_paths

def check_for_special_files():
    """检查项目中是否有特殊配置文件"""
    special_files = []
    
    # 可能的特殊配置文件
    file_patterns = [
        "pip.conf",
        ".piprc",
        ".pip/pip.conf",
        "pyproject.toml",
        "setup.cfg"
    ]
    
    for pattern in file_patterns:
        matches = glob.glob(pattern)
        special_files.extend(matches)
        
    return special_files

def scan_for_install_commands():
    """扫描项目文件中的安装命令"""
    install_commands = []
    
    # 可能包含安装命令的文件
    file_patterns = [
        "*.sh",
        "Dockerfile",
        "Makefile",
        "*.py"
    ]
    
    for pattern in file_patterns:
        for filename in glob.glob(pattern, recursive=True):
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                try:
                    content = f.read()
                    if "pip install" in content and "xywechatpad" in content:
                        # 提取安装命令
                        lines = content.split("\n")
                        for line in lines:
                            if "pip install" in line and "xywechatpad" in line:
                                install_commands.append({
                                    "file": filename,
                                    "command": line.strip()
                                })
                except Exception as e:
                    logger.warning(f"读取文件 {filename} 时出错: {str(e)}")
    
    return install_commands

def restore_installation():
    """尝试恢复原始安装方法"""
    # 检查系统
    sys_info = {
        "system": platform.system(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
        "platform": platform.platform()
    }
    logger.info(f"系统信息: {sys_info}")
    
    # 检查自定义wheels
    wheels = check_for_custom_wheels()
    if wheels:
        logger.info(f"找到 {len(wheels)} 个wheel文件:")
        for wheel in wheels:
            logger.info(f"  - {wheel}")
            
        # 尝试安装找到的第一个xywechatpad wheel
        for wheel in wheels:
            if "xywechatpad" in wheel:
                logger.info(f"尝试安装: {wheel}")
                try:
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", wheel],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        logger.info("安装成功!")
                        return True
                    else:
                        logger.warning(f"安装失败: {result.stderr}")
                except Exception as e:
                    logger.error(f"安装过程出错: {str(e)}")
    
    # 检查特殊配置文件
    special_files = check_for_special_files()
    if special_files:
        logger.info(f"找到 {len(special_files)} 个特殊配置文件:")
        for file in special_files:
            logger.info(f"  - {file}")
    
    # 扫描安装命令
    install_commands = scan_for_install_commands()
    if install_commands:
        logger.info(f"找到 {len(install_commands)} 个安装命令:")
        for cmd in install_commands:
            logger.info(f"  - 在 {cmd['file']} 中: {cmd['command']}")
            
        # 尝试执行找到的命令
        for cmd in install_commands:
            # 提取并清理命令
            command = cmd["command"]
            # 去除前导空格和注释
            command = command.strip()
            if command.startswith("#"):
                continue
                
            # 去除shell语法
            if "pip install" in command:
                parts = command.split("pip install")[1].strip()
                clean_command = f"{sys.executable} -m pip install {parts}"
                
                logger.info(f"尝试执行: {clean_command}")
                try:
                    result = subprocess.run(
                        clean_command,
                        shell=True,
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        logger.info("命令执行成功!")
                        return True
                    else:
                        logger.warning(f"命令执行失败: {result.stderr}")
                except Exception as e:
                    logger.error(f"命令执行出错: {str(e)}")
    
    # 最后尝试常规安装
    logger.info("尝试直接安装 xywechatpad-binary==1.1.0")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "xywechatpad-binary==1.1.0"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            logger.info("直接安装成功!")
            return True
        else:
            logger.warning(f"直接安装失败: {result.stderr}")
    except Exception as e:
        logger.error(f"直接安装出错: {str(e)}")
    
    logger.error("所有恢复尝试均失败")
    return False

def main():
    """主函数"""
    success = restore_installation()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 