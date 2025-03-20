#!/usr/bin/env python3
"""
专门用于下载和安装 xywechatpad-binary wheel 包的脚本
"""
import sys
import os
import subprocess
import logging
import platform
import tempfile
import requests
import hashlib
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("download_wheel")

def get_system_info():
    """获取系统信息"""
    py_version = platform.python_version()
    py_major, py_minor = py_version.split(".")[:2]
    cp_tag = f"cp{py_major}{py_minor}"  # 例如 Python 3.8 -> cp38
    
    return {
        "system": platform.system(),
        "machine": platform.machine(),
        "python_version": py_version,
        "cp_tag": cp_tag,
        "platform": platform.platform()
    }

def get_wheel_urls(sys_info):
    """获取适合当前系统的wheel包下载链接"""
    cp_tag = sys_info["cp_tag"]
    machine = sys_info["machine"]
    
    arch = None
    if "aarch64" in machine or "arm64" in machine:
        arch = "aarch64"
    elif "x86_64" in machine or "amd64" in machine:
        arch = "x86_64"
    else:
        logger.warning(f"未知架构: {machine}, 将尝试aarch64和x86_64")
        # 如果无法确定架构，返回所有可能的架构
        return {
            "aarch64": [
                f"https://mirrors.aliyun.com/pypi/packages/{cp_tag}/x/xywechatpad-binary/xywechatpad_binary-1.1.0-py3-none-manylinux2014_aarch64.whl",
                f"https://pypi.tuna.tsinghua.edu.cn/packages/{cp_tag}/x/xywechatpad-binary/xywechatpad_binary-1.1.0-py3-none-manylinux2014_aarch64.whl"
            ],
            "x86_64": [
                f"https://mirrors.aliyun.com/pypi/packages/{cp_tag}/x/xywechatpad-binary/xywechatpad_binary-1.1.0-py3-none-manylinux2014_x86_64.whl",
                f"https://pypi.tuna.tsinghua.edu.cn/packages/{cp_tag}/x/xywechatpad-binary/xywechatpad_binary-1.1.0-py3-none-manylinux2014_x86_64.whl"
            ]
        }
    
    # 返回特定架构的链接
    return {
        arch: [
            f"https://mirrors.aliyun.com/pypi/packages/{cp_tag}/x/xywechatpad-binary/xywechatpad_binary-1.1.0-py3-none-manylinux2014_{arch}.whl",
            f"https://pypi.tuna.tsinghua.edu.cn/packages/{cp_tag}/x/xywechatpad-binary/xywechatpad_binary-1.1.0-py3-none-manylinux2014_{arch}.whl"
        ]
    }

def download_file(url, dest_path):
    """从URL下载文件"""
    try:
        logger.info(f"正在从 {url} 下载文件...")
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        downloaded = 0
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    # 打印下载进度
                    percent = int(100 * downloaded / total_size) if total_size > 0 else 0
                    sys.stdout.write(f"\r下载进度: {percent}% [{downloaded} / {total_size} 字节]")
                    sys.stdout.flush()
        
        sys.stdout.write("\n")
        logger.info(f"下载完成: {dest_path}")
        return True
    except Exception as e:
        logger.error(f"下载失败: {str(e)}")
        return False

def install_wheel(wheel_path):
    """安装wheel包"""
    try:
        logger.info(f"正在安装wheel: {wheel_path}")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", wheel_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("安装成功!")
            return True
        else:
            logger.error(f"安装失败: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"安装过程出错: {str(e)}")
        return False

def create_wheels_dir():
    """创建wheels目录"""
    wheels_dir = Path("wheels")
    if not wheels_dir.exists():
        logger.info("创建wheels目录")
        wheels_dir.mkdir(parents=True)
    return wheels_dir

def main():
    """主函数"""
    # 获取系统信息
    sys_info = get_system_info()
    logger.info(f"系统信息: {sys_info}")
    
    # 检查Python版本兼容性
    py_version = sys_info["python_version"]
    if py_version.startswith("3.11"):
        logger.warning("⚠️ 警告: xywechatpad-binary 可能不兼容 Python 3.11")
        logger.warning("如果安装失败，请考虑使用 Python 3.8 或 3.9")
    
    # 创建wheels目录
    wheels_dir = create_wheels_dir()
    
    # 尝试直接用pip安装
    logger.info("首先尝试用pip直接安装...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "xywechatpad-binary==1.1.0"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            logger.info("直接安装成功!")
            return 0
        else:
            logger.info("直接安装失败，尝试下载wheel...")
    except Exception:
        pass
    
    # 尝试已有的wheel文件
    wheel_files = list(wheels_dir.glob("xywechatpad_binary*.whl"))
    if wheel_files:
        logger.info(f"找到现有wheel文件: {wheel_files[0]}")
        if install_wheel(wheel_files[0]):
            return 0
    
    # 获取适配当前Python版本的下载链接
    wheel_urls = get_wheel_urls(sys_info)
    
    # 尝试下载并安装
    for arch, urls in wheel_urls.items():
        logger.info(f"尝试下载 {arch} 架构的wheel包...")
        for url in urls:
            filename = url.split("/")[-1]
            wheel_path = wheels_dir / filename
            
            if download_file(url, wheel_path):
                if install_wheel(wheel_path):
                    return 0
    
    # 如果所有尝试都失败，尝试源代码安装
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
    
    logger.error("所有尝试均失败，无法安装 xywechatpad-binary")
    return 1

if __name__ == "__main__":
    sys.exit(main()) 