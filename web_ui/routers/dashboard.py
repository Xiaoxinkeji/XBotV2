from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from sqlalchemy import select, func, desc
from database.models import User, Message, GroupInfo, Plugin, PluginCall
from database.session import get_session
from datetime import datetime, timedelta
from web_ui.utils.system_utils import psutil, HAS_PSUTIL
import platform
import os

router = APIRouter()

@router.get("/")
async def get_dashboard_data():
    """获取仪表盘数据"""
    try:
        async with get_session() as session:
            # 获取基础统计数据
            user_count_query = select(func.count()).select_from(User)
            user_count = await session.scalar(user_count_query) or 0
            
            group_count_query = select(func.count()).select_from(GroupInfo)
            group_count = await session.scalar(group_count_query) or 0
            
            message_count_query = select(func.count()).select_from(Message)
            message_count = await session.scalar(message_count_query) or 0
            
            plugin_count_query = select(func.count()).select_from(Plugin)
            plugin_count = await session.scalar(plugin_count_query) or 0
            
            # 获取今日活跃数据
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            today_message_query = select(func.count()).select_from(Message).where(
                Message.timestamp >= today
            )
            today_message_count = await session.scalar(today_message_query) or 0
            
            today_active_users_query = select(func.count(func.distinct(Message.sender_id))).select_from(Message).where(
                Message.timestamp >= today
            )
            today_active_users = await session.scalar(today_active_users_query) or 0
            
            today_active_groups_query = select(func.count(func.distinct(Message.group_id))).select_from(Message).where(
                Message.timestamp >= today,
                Message.group_id.isnot(None)
            )
            today_active_groups = await session.scalar(today_active_groups_query) or 0
            
            # 获取系统资源使用情况
            system_info = {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "platform": platform.platform(),
                "uptime": int((datetime.now() - datetime.fromtimestamp(psutil.boot_time())).total_seconds())
            }
            
            # 获取最活跃的5个群组
            active_groups_query = select(
                GroupInfo.wxid,
                GroupInfo.name,
                func.count(Message.id).label("message_count")
            ).join(
                Message, 
                Message.group_id == GroupInfo.wxid
            ).where(
                Message.timestamp >= today - timedelta(days=7)
            ).group_by(
                GroupInfo.wxid
            ).order_by(
                desc("message_count")
            ).limit(5)
            
            active_groups_result = await session.execute(active_groups_query)
            active_groups = [
                {"wxid": row.wxid, "name": row.name, "message_count": row.message_count}
                for row in active_groups_result
            ]
            
            # 获取最新10条消息
            recent_messages_query = select(
                Message.id,
                Message.content,
                Message.timestamp,
                Message.sender_id,
                Message.group_id,
                User.nickname.label("sender_name"),
                GroupInfo.name.label("group_name")
            ).outerjoin(
                User, User.wxid == Message.sender_id
            ).outerjoin(
                GroupInfo, GroupInfo.wxid == Message.group_id
            ).order_by(
                desc(Message.timestamp)
            ).limit(10)
            
            recent_messages_result = await session.execute(recent_messages_query)
            recent_messages = [
                {
                    "id": row.id,
                    "content": row.content[:50] + "..." if row.content and len(row.content) > 50 else row.content,
                    "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                    "sender_id": row.sender_id,
                    "sender_name": row.sender_name,
                    "group_id": row.group_id,
                    "group_name": row.group_name
                }
                for row in recent_messages_result
            ]
            
            return {
                "success": True,
                "data": {
                    "stats": {
                        "user_count": user_count,
                        "group_count": group_count,
                        "message_count": message_count,
                        "plugin_count": plugin_count,
                        "today_message_count": today_message_count,
                        "today_active_users": today_active_users,
                        "today_active_groups": today_active_groups
                    },
                    "system": system_info,
                    "active_groups": active_groups,
                    "recent_messages": recent_messages
                }
            }
    except Exception as e:
        raise HTTPException(500, f"获取仪表盘数据失败: {str(e)}") 