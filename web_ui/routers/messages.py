from fastapi import APIRouter, Query
from typing import List, Dict, Any

router = APIRouter()

@router.get("/")
async def get_messages(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """获取消息历史"""
    return {
        "success": True,
        "data": [],
        "pagination": {
            "total": 0,
            "limit": limit,
            "offset": offset
        }
    } 