from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import logging
import sys
import os
import time
import psutil
import json
from datetime import datetime
import asyncio
import platform
import socket
import redis
from WechatAPI import WechatAPIClient
from ..dependencies import get_current_user
from ..utils.redis_utils import check_redis_connection
from ..utils.wechat_utils import check_wechat_connection, ping_wechat_api

router = APIRouter()
logger = logging.getLogger(__name__)

# 微信连接状态缓存，避免频繁检查
wechat_connection_cache = {
    "status": None,
    "last_check": 0,
    "cache_ttl": 30  # 缓存有效期30秒
}

@router.get("/")
async def get_system_status(current_user: Dict = Depends(get_current_user)) -> Dict[str, Any]:
    """
    获取系统状态，包括微信API和Redis连接状态
    """
    try:
        # 获取微信API连接状态（使用缓存机制）
        current_time = time.time()
        if (wechat_connection_cache["status"] is None or 
            current_time - wechat_connection_cache["last_check"] > wechat_connection_cache["cache_ttl"]):
            
            # 重新检查微信API连接状态
            try:
                # 通过多种方式检查以提高可靠性
                wechat_status = await check_wechat_connection()
                
                if not wechat_status:
                    # 如果主方法失败，尝试ping备用API
                    wechat_status = await ping_wechat_api()
                
                wechat_connection_cache["status"] = wechat_status
            except Exception as e:
                logger.error(f"检查微信API状态时出错: {str(e)}")
                wechat_connection_cache["status"] = False
                
            wechat_connection_cache["last_check"] = current_time
        
        # 获取Redis连接状态
        redis_status = await check_redis_connection()
        
        # 系统资源使用情况
        cpu_percent = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 系统信息
        system_info = {
            "os": platform.platform(),
            "python": platform.python_version(),
            "hostname": socket.gethostname()
        }
        
        # 运行时间
        bot_start_time = datetime.fromtimestamp(psutil.Process(os.getpid()).create_time())
        uptime_seconds = (datetime.now() - bot_start_time).total_seconds()
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        uptime_info = {
            "days": int(days),
            "hours": int(hours),
            "minutes": int(minutes),
            "seconds": int(seconds),
            "uptime_string": f"{int(days)}天 {int(hours)}小时 {int(minutes)}分钟"
        }
        
        # 微信状态
        wechat_status_info = {
            "logged_in": False,
            "account_info": None
        }
        
        try:
            client = WechatAPIClient()
            result = client.get_login_info()
            if result and result.get("success"):
                wechat_status_info["logged_in"] = True
                wechat_status_info["account_info"] = {
                    "wxid": result.get("data", {}).get("wxid"),
                    "nickname": result.get("data", {}).get("nickname"),
                    "avatar": result.get("data", {}).get("avatar")
                }
        except Exception as e:
            wechat_status_info["error"] = str(e)
        
        # 格式化返回数据
        return {
            "code": 200,
            "message": "获取系统状态成功",
            "data": {
                "services": {
                    "wechat_api": wechat_connection_cache["status"],
                    "redis": redis_status
                },
                "resources": {
                    "cpu": {
                        "percent": cpu_percent
                    },
                    "memory": {
                        "total": memory.total,
                        "available": memory.available,
                        "percent": memory.percent
                    },
                    "disk": {
                        "total": disk.total,
                        "free": disk.free,
                        "percent": disk.percent
                    }
                },
                "system": system_info,
                "uptime": uptime_info,
                "wechat": wechat_status_info,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
    except Exception as e:
        logger.error(f"获取系统状态时出错: {str(e)}")
        return {
            "code": 500,
            "message": f"获取系统状态失败: {str(e)}",
            "data": None
        }

@router.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok"} 