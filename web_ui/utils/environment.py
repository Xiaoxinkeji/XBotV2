import os
from typing import Dict, Any, Optional

# 微信API配置
WECHAT_API_HOST = os.getenv("WECHAT_API_HOST", "localhost")
WECHAT_API_PORT = int(os.getenv("WECHAT_API_PORT", "5000"))
WECHAT_API_URL = f"http://{WECHAT_API_HOST}:{WECHAT_API_PORT}/api"
WECHAT_API_TOKEN = os.getenv("WECHAT_API_TOKEN", "")

# Redis配置
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

# 服务恢复配置
WECHAT_SERVICE_NAME = os.getenv("WECHAT_SERVICE_NAME", "wechat-service")
MAX_RECOVERY_ATTEMPTS = int(os.getenv("MAX_RECOVERY_ATTEMPTS", "3"))

def get_env_config() -> Dict[str, Any]:
    """获取当前环境配置"""
    return {
        "wechat_api": {
            "host": WECHAT_API_HOST,
            "port": WECHAT_API_PORT,
            "url": WECHAT_API_URL,
            "token": WECHAT_API_TOKEN
        },
        "redis": {
            "host": REDIS_HOST,
            "port": REDIS_PORT,
            "db": REDIS_DB,
            "password": REDIS_PASSWORD
        },
        "service": {
            "wechat_service_name": WECHAT_SERVICE_NAME,
            "max_recovery_attempts": MAX_RECOVERY_ATTEMPTS
        }
    }

def update_env_from_config(config: Dict[str, Any]) -> None:
    """从配置文件更新环境变量"""
    if not config:
        return
        
    # 更新微信API配置
    if "wechat_api" in config:
        wechat_config = config["wechat_api"]
        if "host" in wechat_config:
            os.environ["WECHAT_API_HOST"] = str(wechat_config["host"])
        if "port" in wechat_config:
            os.environ["WECHAT_API_PORT"] = str(wechat_config["port"])
        if "token" in wechat_config:
            os.environ["WECHAT_API_TOKEN"] = str(wechat_config["token"])
    
    # 更新Redis配置
    if "redis" in config:
        redis_config = config["redis"]
        if "host" in redis_config:
            os.environ["REDIS_HOST"] = str(redis_config["host"])
        if "port" in redis_config:
            os.environ["REDIS_PORT"] = str(redis_config["port"])
        if "db" in redis_config:
            os.environ["REDIS_DB"] = str(redis_config["db"])
        if "password" in redis_config:
            os.environ["REDIS_PASSWORD"] = str(redis_config["password"]) 