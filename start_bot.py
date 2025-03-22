#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
XBotV2 启动脚本
这个脚本用于启动机器人核心服务和Web界面
"""

import os
import sys
import asyncio
from pathlib import Path

# 设置工作目录
script_dir = Path(__file__).resolve().parent
os.chdir(script_dir)

# 导入日志系统
from loguru import logger
logger.remove()

logger.level("API", no=1, color="<cyan>")

logger.add(
    "logs/XYBot_{time}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    encoding="utf-8",
    enqueue=True,
    retention="2 weeks",
    rotation="00:01",
    backtrace=True,
    diagnose=True,
    level="DEBUG",
)
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
    level="TRACE",
    enqueue=True,
    backtrace=True,
    diagnose=True,
)

async def main():
    """程序入口函数"""
    try:
        # 导入web模块的启动函数
        from web.app import start_web_server
        
        # 打印启动信息
        print("=" * 50)
        print("   XBotV2 启动中...")
        print("=" * 50)
        
        # 打印服务信息
        logger.info("正在启动 XBotV2...")
        
        # 首先启动Web服务
        logger.info("正在启动Web服务...")
        web_thread = asyncio.create_task(asyncio.to_thread(start_web_server))
        
        # 等待Web服务启动完成
        await asyncio.sleep(3)
        logger.success("Web服务启动成功！")
        
        # 提示用户访问Web界面
        print("\n您可以通过浏览器访问 http://localhost:8080 来管理XBotV2")
        print("默认用户名：admin，默认密码：admin123")
        print("请注意及时修改默认密码以确保安全\n")
        
        # 等待任务完成
        await web_thread
        
    except KeyboardInterrupt:
        logger.info("收到用户终止信号，正在关闭服务...")
        
    except Exception as e:
        logger.error(f"启动过程中发生错误: {e}")
        logger.exception("详细错误信息：")
        
    finally:
        logger.info("XBotV2 已关闭")

if __name__ == "__main__":
    # 启动主程序
    asyncio.run(main()) 