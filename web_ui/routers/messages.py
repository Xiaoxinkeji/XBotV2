from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func, desc
from database.models import Message, User, GroupInfo
from database.session import get_session
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/")
async def get_messages(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sender: Optional[str] = None,
    group: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    keyword: Optional[str] = None
):
    """获取消息历史"""
    try:
        async with get_session() as session:
            # 基本查询
            query = select(Message).order_by(desc(Message.timestamp))
            count_query = select(func.count()).select_from(Message)
            
            # 添加筛选条件
            filters = []
            if sender:
                filters.append(Message.sender_wxid == sender)
            if group:
                filters.append(Message.group_wxid == group)
            
            # 时间筛选
            if start_time:
                try:
                    start_dt = datetime.fromisoformat(start_time)
                    filters.append(Message.timestamp >= start_dt)
                except ValueError:
                    pass
                    
            if end_time:
                try:
                    end_dt = datetime.fromisoformat(end_time)
                    filters.append(Message.timestamp <= end_dt)
                except ValueError:
                    pass
            
            # 关键词筛选
            if keyword:
                filters.append(Message.content.like(f"%{keyword}%"))
                
            # 应用所有筛选条件
            if filters:
                for f in filters:
                    query = query.filter(f)
                    count_query = count_query.filter(f)
            
            # 获取总数
            total_result = await session.execute(count_query)
            total = total_result.scalar() or 0
            
            # 分页
            query = query.offset(offset).limit(limit)
            
            # 执行查询
            result = await session.execute(query)
            messages = result.scalars().all()
            
            # 获取相关用户和群组信息
            user_wxids = set()
            group_wxids = set()
            
            for msg in messages:
                if msg.sender_wxid:
                    user_wxids.add(msg.sender_wxid)
                if msg.receiver_wxid and msg.type != 'group':
                    user_wxids.add(msg.receiver_wxid)
                if msg.group_wxid:
                    group_wxids.add(msg.group_wxid)
            
            # 查询用户信息
            users = {}
            if user_wxids:
                user_query = select(User).filter(User.wxid.in_(user_wxids))
                user_result = await session.execute(user_query)
                for user in user_result.scalars():
                    users[user.wxid] = {
                        "nickname": user.nickname,
                        "avatar": user.avatar_url
                    }
            
            # 查询群组信息
            groups = {}
            if group_wxids:
                group_query = select(GroupInfo).filter(GroupInfo.wxid.in_(group_wxids))
                group_result = await session.execute(group_query)
                for group in group_result.scalars():
                    groups[group.wxid] = {
                        "name": group.name
                    }
            
            # 转换为字典列表
            message_list = []
            for msg in messages:
                message_dict = {
                    "id": msg.id,
                    "type": msg.type,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "sender": {
                        "wxid": msg.sender_wxid,
                        "nickname": users.get(msg.sender_wxid, {}).get("nickname", "未知用户"),
                        "avatar": users.get(msg.sender_wxid, {}).get("avatar", "")
                    }
                }
                
                if msg.type == 'group':
                    message_dict["group"] = {
                        "wxid": msg.group_wxid,
                        "name": groups.get(msg.group_wxid, {}).get("name", "未知群组")
                    }
                else:
                    message_dict["receiver"] = {
                        "wxid": msg.receiver_wxid,
                        "nickname": users.get(msg.receiver_wxid, {}).get("nickname", "未知用户"),
                        "avatar": users.get(msg.receiver_wxid, {}).get("avatar", "")
                    }
                    
                message_list.append(message_dict)
            
            return {
                "success": True,
                "data": message_list,
                "pagination": {
                    "total": total,
                    "limit": limit,
                    "offset": offset
                }
            }
    except Exception as e:
        raise HTTPException(500, f"获取消息历史失败: {str(e)}")

@router.get("/stats")
async def get_message_stats(
    days: int = Query(7, ge=1, le=30),
    group_wxid: Optional[str] = None
):
    """获取消息统计数据"""
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        async with get_session() as session:
            # 按日期统计消息数量
            daily_stats = []
            for i in range(days):
                day_start = start_time + timedelta(days=i)
                day_end = day_start + timedelta(days=1)
                
                query = select(func.count()).select_from(Message).filter(
                    Message.timestamp >= day_start,
                    Message.timestamp < day_end
                )
                
                if group_wxid:
                    query = query.filter(Message.group_wxid == group_wxid)
                    
                result = await session.execute(query)
                count = result.scalar() or 0
                
                daily_stats.append({
                    "date": day_start.strftime("%Y-%m-%d"),
                    "count": count
                })
            
            # 统计最活跃群组
            top_groups_query = select(
                Message.group_wxid,
                func.count().label("message_count")
            ).filter(
                Message.timestamp >= start_time,
                Message.group_wxid.isnot(None)
            ).group_by(
                Message.group_wxid
            ).order_by(
                desc("message_count")
            ).limit(5)
            
            top_groups_result = await session.execute(top_groups_query)
            top_groups_raw = top_groups_result.all()
            
            # 获取群组名称
            group_wxids = [g[0] for g in top_groups_raw if g[0]]
            group_query = select(GroupInfo).filter(GroupInfo.wxid.in_(group_wxids))
            group_result = await session.execute(group_query)
            groups = {g.wxid: g.name for g in group_result.scalars()}
            
            top_groups = [
                {
                    "wxid": g[0],
                    "name": groups.get(g[0], "未知群组"),
                    "message_count": g[1]
                }
                for g in top_groups_raw if g[0]
            ]
            
            # 统计最活跃用户
            top_users_query = select(
                Message.sender_wxid,
                func.count().label("message_count")
            ).filter(
                Message.timestamp >= start_time,
                Message.sender_wxid.isnot(None)
            )
            
            if group_wxid:
                top_users_query = top_users_query.filter(Message.group_wxid == group_wxid)
                
            top_users_query = top_users_query.group_by(
                Message.sender_wxid
            ).order_by(
                desc("message_count")
            ).limit(5)
            
            top_users_result = await session.execute(top_users_query)
            top_users_raw = top_users_result.all()
            
            # 获取用户名称
            user_wxids = [u[0] for u in top_users_raw if u[0]]
            user_query = select(User).filter(User.wxid.in_(user_wxids))
            user_result = await session.execute(user_query)
            users = {u.wxid: u.nickname for u in user_result.scalars()}
            
            top_users = [
                {
                    "wxid": u[0],
                    "nickname": users.get(u[0], "未知用户"),
                    "message_count": u[1]
                }
                for u in top_users_raw if u[0]
            ]
            
            return {
                "success": True,
                "data": {
                    "daily_stats": daily_stats,
                    "top_groups": top_groups,
                    "top_users": top_users,
                    "total_messages": sum(d["count"] for d in daily_stats)
                }
            }
    except Exception as e:
        raise HTTPException(500, f"获取消息统计失败: {str(e)}") 