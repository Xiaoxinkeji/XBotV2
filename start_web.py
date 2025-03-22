import os
import sys
from pathlib import Path

# 设置工作目录为脚本所在目录
script_dir = Path(__file__).resolve().parent
os.chdir(script_dir)

# 添加日志信息
from loguru import logger
logger.remove()

logger.level("API", no=1, color="<cyan>")

logger.add(
    "logs/XYBot_web_{time}.log",
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

if __name__ == "__main__":
    print("警告：直接启动Web服务可能导致Web界面无法获取机器人状态信息。")
    print("建议使用 'python main.py' 来启动完整程序，它会确保按正确顺序启动机器人和Web界面。")
    user_choice = input("是否仍要继续启动单独的Web服务？(y/n): ")
    
    if user_choice.lower() == 'y':
        print("启动 Web 服务器...")
        logger.info("启动 Web 服务器...")
        # 直接导入并调用web.app中的函数
        from web.app import start_web_server
        start_web_server()
    else:
        print("操作已取消。请使用 'python main.py' 启动完整程序。")
        sys.exit(0) 