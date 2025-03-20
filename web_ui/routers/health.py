from fastapi import APIRouter
import psutil
import redis
from WechatAPI import WechatAPIClient

router = APIRouter()

@router.get("/")
async def health_check():
    """系统健康检查"""
    health = {
        "status": "ok",
        "services": {
            "web": True,
            "redis": False,
            "wechat_api": False
        },
        "details": {}
    }
    
    # 检查Redis状态
    try:
        r = redis.Redis(host="127.0.0.1", port=6379, db=0)
        if r.ping():
            health["services"]["redis"] = True
    except Exception as e:
        health["details"]["redis_error"] = str(e)
    
    # 检查WechatAPI状态
    try:
        client = WechatAPIClient()
        result = client.get_login_info()
        if result and result.get("success"):
            health["services"]["wechat_api"] = True
    except Exception as e:
        health["details"]["wechat_api_error"] = str(e)
    
    return health 