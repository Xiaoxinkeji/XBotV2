import os
import logging
import json
import asyncio
import aiohttp
from typing import Dict, Any, Optional, Tuple, List
import time
from WechatAPI import WechatAPIClient

logger = logging.getLogger(__name__)

# 配置信息 - 应该从环境变量或配置文件中获取
WECHAT_API_HOST = os.getenv("WECHAT_API_HOST", "localhost")
WECHAT_API_PORT = int(os.getenv("WECHAT_API_PORT", "5000"))
WECHAT_API_URL = f"http://{WECHAT_API_HOST}:{WECHAT_API_PORT}/api"

# 连接状态缓存
connection_status = {
    "status": False,
    "last_check": 0,
    "retry_count": 0,
    "max_retries": 3
}

async def check_wechat_connection() -> bool:
    """检查微信API连接状态，使用官方客户端API"""
    try:
        # 如果之前检查失败次数过多且时间很近，直接返回False避免频繁请求
        current_time = time.time()
        if (connection_status["retry_count"] >= connection_status["max_retries"] and 
            current_time - connection_status["last_check"] < 60):
            return False
        
        # 使用微信官方客户端检查连接
        client = WechatAPIClient(WECHAT_API_HOST, WECHAT_API_PORT)
        is_running = await client.is_running()
        
        if is_running:
            # 重置失败计数
            connection_status["retry_count"] = 0
            connection_status["status"] = True
            connection_status["last_check"] = current_time
            return True
        else:
            logger.warning(f"微信API服务未运行")
            connection_status["retry_count"] += 1
            connection_status["status"] = False
            connection_status["last_check"] = current_time
            return False
    except Exception as e:
        logger.error(f"检查微信API连接时出错: {str(e)}")
        connection_status["retry_count"] += 1
        connection_status["status"] = False
        connection_status["last_check"] = time.time()
        return False

async def ping_wechat_api() -> bool:
    """使用轻量级的ping方式检查微信API连接状态"""
    try:
        timeout = aiohttp.ClientTimeout(total=2)  # 更短的超时
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # 尝试简单的HTTP请求
            async with session.get(f"http://{WECHAT_API_HOST}:{WECHAT_API_PORT}/IsRunning") as response:
                if response.status == 200:
                    return await response.text() == 'OK'
                return False
    except Exception as e:
        logger.debug(f"微信API ping检查失败: {str(e)}")
        return False

async def get_wechat_status() -> Dict[str, Any]:
    """获取微信机器人完整状态"""
    try:
        # 使用官方客户端获取详细状态
        client = WechatAPIClient(WECHAT_API_HOST, WECHAT_API_PORT)
        is_running = await client.is_running()
        
        if not is_running:
            return {
                "status": "error",
                "message": "微信API服务未运行",
                "is_running": False,
                "is_logged_in": False
            }
        
        # 检查是否已登录
        try:
            login_info = await client.get_login_info()
            is_logged_in = login_info.get("is_logged_in", False) if login_info.get("success") else False
            
            return {
                "status": "ok",
                "message": "微信API服务正常",
                "is_running": True,
                "is_logged_in": is_logged_in,
                "login_info": login_info.get("data") if login_info.get("success") else None
            }
        except Exception as e:
            return {
                "status": "partial",
                "message": f"微信API服务运行中，但获取登录状态失败: {str(e)}",
                "is_running": True,
                "is_logged_in": False
            }
    except Exception as e:
        logger.error(f"获取微信状态时出错: {str(e)}")
        return {"status": "error", "message": str(e), "is_running": False, "is_logged_in": False}

async def init_wechat_connection():
    """初始化微信连接和配置"""
    # 这个函数可以在应用启动时调用，确保微信API正确初始化
    logger.info("正在初始化微信API连接...")
    is_connected = await check_wechat_connection()
    if is_connected:
        logger.info("微信API连接成功")
    else:
        logger.warning("微信API连接失败，将在后续请求中重试")
        
    return is_connected 