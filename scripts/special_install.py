#!/usr/bin/env python3
"""
特殊包安装工具
"""
import sys
import os
import subprocess
import logging
import argparse
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("special_install")

def find_package_sources(package_name, search_dirs=None):
    """查找包的可能来源"""
    if search_dirs is None:
        search_dirs = [
            ".",
            "wheels",
            "dist",
            "WechatAPIDocs",
            "dependencies",
            "vendor"
        ]
    
    sources = []
    
    # 查找目录和wheel文件
    for search_dir in search_dirs:
        if not os.path.exists(search_dir):
            continue
            
        # 检查是否是包目录
        if os.path.basename(search_dir) == package_name and os.path.isdir(search_dir):
            sources.append(("directory", search_dir))
            continue
            
        # 检查子目录
        package_dir = os.path.join(search_dir, package_name)
        if os.path.isdir(package_dir):
            sources.append(("directory", package_dir))
            
        # 检查wheel文件
        if os.path.isdir(search_dir):
            for filename in os.listdir(search_dir):
                if filename.startswith(f"{package_name}-") and filename.endswith(".whl"):
                    sources.append(("wheel", os.path.join(search_dir, filename)))
                    
        # 检查requirements.txt文件
        req_file = os.path.join(search_dir, "requirements.txt")
        if os.path.isfile(req_file):
            with open(req_file, "r") as f:
                for line in f:
                    if line.strip().startswith(package_name):
                        sources.append(("requirement", req_file))
                        break
    
    return sources

def install_package(package_name, version=None, method=None, source=None):
    """
    尝试安装指定的包
    
    :param package_name: 包名
    :param version: 版本号(可选)
    :param method: 安装方法(pypi, wheel, directory, requirement)
    :param source: 安装源(文件或目录路径)
    :return: 是否成功
    """
    try:
        if method == "pypi":
            spec = f"{package_name}=={version}" if version else package_name
            logger.info(f"从PyPI安装 {spec}")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", spec, "--no-cache-dir"],
                capture_output=True,
                text=True
            )
        elif method == "wheel" and source:
            logger.info(f"从wheel安装 {os.path.basename(source)}")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", source],
                capture_output=True,
                text=True
            )
        elif method == "directory" and source:
            logger.info(f"从目录安装 {source}")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-e", source],
                capture_output=True,
                text=True
            )
        elif method == "requirement" and source:
            logger.info(f"从requirements文件安装 {source}")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", source],
                capture_output=True,
                text=True
            )
        else:
            logger.error(f"无效的安装方法: {method}")
            return False
            
        if result.returncode == 0:
            logger.info("安装成功")
            return True
        else:
            logger.error(f"安装失败: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"安装过程出错: {str(e)}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="特殊包安装工具")
    parser.add_argument("package", help="要安装的包名")
    parser.add_argument("--version", help="包版本号")
    parser.add_argument("--method", choices=["auto", "pypi", "wheel", "directory", "requirement"],
                      default="auto", help="安装方法")
    parser.add_argument("--source", help="安装源(文件或目录路径)")
    
    args = parser.parse_args()
    
    if args.method == "auto":
        # 自动查找并尝试安装
        logger.info(f"正在查找 {args.package} 的来源...")
        sources = find_package_sources(args.package)
        
        if not sources:
            logger.warning(f"未找到 {args.package} 的来源，尝试从PyPI安装")
            if install_package(args.package, args.version, "pypi", None):
                return 0
            else:
                logger.error(f"无法安装 {args.package}")
                return 1
                
        logger.info(f"找到 {len(sources)} 个可能的来源")
        for method, source in sources:
            logger.info(f"尝试从 {method} 安装: {source}")
            if install_package(args.package, args.version, method, source):
                return 0
                
        logger.error(f"尝试了所有可能的来源，但无法安装 {args.package}")
        return 1
    else:
        # 使用指定的方法安装
        if install_package(args.package, args.version, args.method, args.source):
            return 0
        else:
            return 1

if __name__ == "__main__":
    sys.exit(main()) 