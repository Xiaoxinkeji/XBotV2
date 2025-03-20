from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Dict, Any, Optional
import os
import json
from pathlib import Path
from sqlalchemy import select, func
from database.models import User, GroupInfo, GroupMember
from database.session import get_session
from bot_core import bot_core

router = APIRouter()

@router.get("/")
async def get_all_users(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    keyword: Optional[str] = None
):
    """获取所有用户信息"""
    try:
        async with get_session() as session:
            # 基本查询
            query = select(User)
            count_query = select(func.count()).select_from(User)
            
            # 添加筛选条件
            if keyword:
                query = query.filter(User.nickname.like(f"%{keyword}%") | User.wxid.like(f"%{keyword}%"))
                count_query = count_query.filter(User.nickname.like(f"%{keyword}%") | User.wxid.like(f"%{keyword}%"))
                
            # 获取总数
            total_result = await session.execute(count_query)
            total = total_result.scalar() or 0
            
            # 分页
            query = query.offset(offset).limit(limit)
            
            # 执行查询
            result = await session.execute(query)
            users = result.scalars().all()
            
            # 转换为字典列表
            user_list = [
                {
                    "wxid": user.wxid,
                    "nickname": user.nickname,
                    "avatar": user.avatar_url or "",
                    "points": user.points,
                    "sign_in_count": user.sign_in_count,
                    "last_sign_in": user.last_sign_in.isoformat() if user.last_sign_in else None
                }
                for user in users
            ]
            
            return {
                "success": True,
                "data": user_list,
                "pagination": {
                    "total": total,
                    "limit": limit,
                    "offset": offset
                }
            }
    except Exception as e:
        raise HTTPException(500, f"获取用户信息失败: {str(e)}")

@router.get("/groups")
async def get_all_groups(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    keyword: Optional[str] = None
):
    """获取所有群组信息"""
    try:
        async with get_session() as session:
            # 基本查询
            query = select(GroupInfo)
            count_query = select(func.count()).select_from(GroupInfo)
            
            # 添加筛选条件
            if keyword:
                query = query.filter(GroupInfo.name.like(f"%{keyword}%") | GroupInfo.wxid.like(f"%{keyword}%"))
                count_query = count_query.filter(GroupInfo.name.like(f"%{keyword}%") | GroupInfo.wxid.like(f"%{keyword}%"))
                
            # 获取总数
            total_result = await session.execute(count_query)
            total = total_result.scalar() or 0
            
            # 分页
            query = query.offset(offset).limit(limit)
            
            # 执行查询
            result = await session.execute(query)
            groups = result.scalars().all()
            
            # 转换为字典列表
            group_list = [
                {
                    "wxid": group.wxid,
                    "name": group.name,
                    "member_count": group.member_count,
                    "owner_wxid": group.owner_wxid,
                    "announcement": group.announcement or ""
                }
                for group in groups
            ]
            
            return {
                "success": True,
                "data": group_list,
                "pagination": {
                    "total": total,
                    "limit": limit,
                    "offset": offset
                }
            }
    except Exception as e:
        raise HTTPException(500, f"获取群组信息失败: {str(e)}")

@router.get("/groups/{group_wxid}/members")
async def get_group_members(
    group_wxid: str,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """获取群成员信息"""
    try:
        async with get_session() as session:
            # 检查群是否存在
            group_query = select(GroupInfo).filter(GroupInfo.wxid == group_wxid)
            group_result = await session.execute(group_query)
            group = group_result.scalar_one_or_none()
            
            if not group:
                raise HTTPException(404, f"群组 {group_wxid} 不存在")
            
            # 查询群成员
            member_query = select(GroupMember).filter(GroupMember.group_wxid == group_wxid)
            count_query = select(func.count()).select_from(GroupMember).filter(GroupMember.group_wxid == group_wxid)
            
            # 获取总数
            total_result = await session.execute(count_query)
            total = total_result.scalar() or 0
            
            # 分页
            member_query = member_query.offset(offset).limit(limit)
            
            # 执行查询
            result = await session.execute(member_query)
            members = result.scalars().all()
            
            # 转换为字典列表
            member_list = [
                {
                    "wxid": member.wxid,
                    "nickname": member.nickname,
                    "group_nickname": member.group_nickname or "",
                    "join_time": member.join_time.isoformat() if member.join_time else None,
                    "is_admin": member.is_admin
                }
                for member in members
            ]
            
            return {
                "success": True,
                "data": {
                    "group": {
                        "wxid": group.wxid,
                        "name": group.name,
                        "member_count": group.member_count
                    },
                    "members": member_list
                },
                "pagination": {
                    "total": total,
                    "limit": limit,
                    "offset": offset
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"获取群成员信息失败: {str(e)}")

@router.post("/update-points")
async def update_user_points(data: Dict[str, Any] = Body(...)):
    """更新用户积分"""
    try:
        wxid = data.get("wxid")
        points = data.get("points")
        
        if not wxid or points is None:
            raise HTTPException(400, "缺少必要参数")
            
        async with get_session() as session:
            # 查找用户
            user_query = select(User).filter(User.wxid == wxid)
            user_result = await session.execute(user_query)
            user = user_result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(404, f"用户 {wxid} 不存在")
                
            # 更新积分
            user.points = points
            await session.commit()
            
            return {
                "success": True,
                "message": f"用户 {user.nickname} 积分已更新为 {points}"
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"更新用户积分失败: {str(e)}")

@router.get("/whitelist")
async def get_whitelist():
    """获取白名单列表"""
    try:
        whitelist_file = Path("plugins/AdminWhitelist/data/whitelist.json")
        if not whitelist_file.exists():
            return {"success": True, "data": []}
            
        with open(whitelist_file, "r", encoding="utf-8") as f:
            whitelist = json.load(f)
            
        return {"success": True, "data": whitelist}
    except Exception as e:
        raise HTTPException(500, f"获取白名单失败: {str(e)}")

@router.post("/whitelist")
async def update_whitelist(whitelist: List[str] = Body(...)):
    """更新白名单列表"""
    try:
        whitelist_dir = Path("plugins/AdminWhitelist/data")
        whitelist_dir.mkdir(exist_ok=True, parents=True)
        
        whitelist_file = whitelist_dir / "whitelist.json"
        
        # 备份原文件
        if whitelist_file.exists():
            with open(whitelist_file, "r", encoding="utf-8") as f:
                old_whitelist = json.load(f)
                
            with open(f"{whitelist_file}.bak", "w", encoding="utf-8") as f:
                json.dump(old_whitelist, f, ensure_ascii=False, indent=2)
        
        # 写入新白名单
        with open(whitelist_file, "w", encoding="utf-8") as f:
            json.dump(whitelist, f, ensure_ascii=False, indent=2)
            
        return {"success": True, "message": "白名单更新成功"}
    except Exception as e:
        raise HTTPException(500, f"更新白名单失败: {str(e)}") 