"""
XYBot Web管理界面 - 主启动脚本
此脚本启动Web管理界面服务
"""

import os
import uvicorn
import logging
from dotenv import load_dotenv
import argparse

# 解析命令行参数
parser = argparse.ArgumentParser(description='启动XYBot Web管理界面')
parser.add_argument('--host', help='主机地址')
parser.add_argument('--port', type=int, help='端口号')
parser.add_argument('--debug', action='store_true', help='启用调试模式')
args = parser.parse_args()

# 加载环境变量
load_dotenv()

# 配置日志
log_level = logging.DEBUG if os.getenv("DEBUG") == "true" or args.debug else logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(asctime)s | %(levelname)s | [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('web_ui.log')
    ]
)

logger = logging.getLogger("web_ui.main")

def main():
    """启动Web管理界面"""
    # 命令行参数优先级高于环境变量
    host = args.host or os.getenv("WEB_HOST", "127.0.0.1")
    port = args.port or int(os.getenv("WEB_PORT", 8080))
    debug = args.debug or (os.getenv("DEBUG") == "true")
    
    logger.info(f"启动XYBot Web管理界面 - http://{host}:{port}")
    if debug:
        logger.info("调试模式已启用")
    logger.info(f"默认管理员账户: admin (首次使用请修改默认密码)")
    
    uvicorn.run(
        "web_ui.app:app",
        host=host,
        port=port,
        reload=debug
    )

if __name__ == "__main__":
    main() 