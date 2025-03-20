from fastapi import APIRouter, HTTPException
import psutil
import platform
import os
import sys
import time
from datetime import datetime, timedelta
import socket
import redis
from WechatAPI import WechatAPIClient

router = APIRouter()

@router.get("/")
async def get_system_status():
    """获取系统状态"""
    try:
        # 系统信息
        system_info = {
            "os": platform.platform(),
            "python": platform.python_version(),
            "hostname": socket.gethostname()
        }
        
        # 资源使用情况
        memory = psutil.virtual_memory()
        memory_info = {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used,
            "free": memory.free
        }
        
        disk = psutil.disk_usage('/')
        disk_info = {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        }
        
        cpu_info = {
            "percent": psutil.cpu_percent(interval=0.1),
            "count": psutil.cpu_count(),
            "load_avg": list(psutil.getloadavg())
        }
        
        # 运行时间
        bot_start_time = datetime.fromtimestamp(psutil.Process(os.getpid()).create_time())
        uptime_seconds = (datetime.now() - bot_start_time).total_seconds()
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        uptime_info = {
            "start_time": bot_start_time.isoformat(),
            "uptime": {
                "days": int(days),
                "hours": int(hours),
                "minutes": int(minutes),
                "seconds": int(seconds)
            },
            "uptime_string": f"{int(days)}天 {int(hours)}小时 {int(minutes)}分钟 {int(seconds)}秒"
        }
        
        # 微信状态
        wechat_status = {
            "logged_in": False,
            "account_info": None
        }
        
        try:
            client = WechatAPIClient()
            result = client.get_login_info()
            if result and result.get("success"):
                wechat_status["logged_in"] = True
                wechat_status["account_info"] = {
                    "wxid": result.get("data", {}).get("wxid"),
                    "nickname": result.get("data", {}).get("nickname"),
                    "avatar": result.get("data", {}).get("avatar")
                }
        except Exception as e:
            wechat_status["error"] = str(e)
        
        # Redis状态
        redis_status = {
            "connected": False
        }
        
        try:
            r = redis.Redis(host="127.0.0.1", port=6379, db=0)
            if r.ping():
                redis_status["connected"] = True
                redis_status["info"] = r.info()
                redis_status["memory_used"] = r.info()["used_memory_human"]
                redis_status["clients_connected"] = r.info()["connected_clients"]
        except Exception as e:
            redis_status["error"] = str(e)
            
        return {
            "success": True,
            "data": {
                "system": system_info,
                "memory": memory_info,
                "disk": disk_info,
                "cpu": cpu_info,
                "uptime": uptime_info,
                "wechat": wechat_status,
                "redis": redis_status
            }
        }
        
    except Exception as e:
        raise HTTPException(500, f"获取系统状态失败: {str(e)}")

@router.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok"} 