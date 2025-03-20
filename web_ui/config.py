import os
import tomli
from pydantic import BaseModel
from typing import List, Optional
import logging

logger = logging.getLogger("web_ui.config")

class WebConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8080
    debug: bool = False
    log_level: str = "info"
    admin_username: str = "admin"
    admin_password: str = "admin123"
    enable_password_login: bool = True
    enable_ip_whitelist: bool = False
    session_expiry_hours: int = 2
    remember_me_days: int = 7
    cors_origins: List[str] = ["*"]
    trusted_hosts: List[str] = ["localhost", "127.0.0.1"]

def load_config() -> WebConfig:
    """加载Web配置"""
    config_path = os.environ.get("CONFIG_PATH", "main_config.toml")
    
    if not os.path.exists(config_path):
        logger.warning(f"配置文件 {config_path} 不存在，使用默认配置")
        return WebConfig()
    
    try:
        with open(config_path, "rb") as f:
            config_data = tomli.load(f)
        
        web_config = config_data.get("web", {})
        return WebConfig(**web_config)
    except Exception as e:
        logger.error(f"加载配置失败: {str(e)}")
        return WebConfig()

# 全局配置实例
config = load_config() 