from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

router = APIRouter()

@router.get("/")
async def get_all_users():
    """获取所有用户信息"""
    try:
        # 后续实现
        return {
            "success": True,
            "data": []
        }
    except Exception as e:
        raise HTTPException(500, f"获取用户信息失败: {str(e)}") 