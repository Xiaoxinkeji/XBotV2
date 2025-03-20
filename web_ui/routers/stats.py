from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter()

@router.get("/")
async def get_stats():
    """获取系统统计信息"""
    return {
        "success": True,
        "data": {
            "total_users": 0,
            "total_messages": 0,
            "active_plugins": 0
        }
    } 