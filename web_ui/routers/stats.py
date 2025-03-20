from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func, desc, distinct
from database.models import Message, User, GroupInfo, Plugin, PluginCall
from database.session import get_session
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/")
async def get_statistics():
    """获取系统统计数据"""
    try:
        async with get_session() as session:
            # 获取用户总数
            user_count_query = select(func.count()).select_from(User)
            user_count_result = await session.execute(user_count_query)
            user_count = user_count_result.scalar() or 0
            
            # 获取群组总数
            group_count_query = select(func.count()).select_from(GroupInfo)
            group_count_result = await session.execute(group_count_query)
            group_count = group_count_result.scalar() or 0
            
            # 获取消息总数
            message_count_query = select(func.count()).select_from(Message)
            message_count_result = await session.execute(message_count_query)
            message_count = message_count_result.scalar() or 0
            
            # 获取24小时内的消息数
            one_day_ago = datetime.now() - timedelta(days=1)
            recent_message_query = select(func.count()).select_from(Message).where(
                Message.timestamp >= one_day_ago
            )
            recent_message_result = await session.execute(recent_message_query)
            recent_message_count = recent_message_result.scalar() or 0
            
            # 获取插件数量
            plugin_count_query = select(func.count()).select_from(Plugin)
            plugin_count_result = await session.execute(plugin_count_query)
            plugin_count = plugin_count_result.scalar() or 0
            
            # 获取启用的插件数量
            enabled_plugin_query = select(func.count()).select_from(Plugin).where(
                Plugin.enabled == True
            )
            enabled_plugin_result = await session.execute(enabled_plugin_query)
            enabled_plugin_count = enabled_plugin_result.scalar() or 0
            
            # 获取每日消息趋势 (最近7天)
            seven_days_ago = datetime.now() - timedelta(days=7)
            daily_message_query = select(
                func.date(Message.timestamp).label("date"),
                func.count().label("count")
            ).where(
                Message.timestamp >= seven_days_ago
            ).group_by(
                func.date(Message.timestamp)
            ).order_by(
                "date"
            )
            
            daily_message_result = await session.execute(daily_message_query)
            daily_message_rows = daily_message_result.all()
            
            daily_message_count = []
            current_date = seven_days_ago.date()
            end_date = datetime.now().date()
            
            while current_date <= end_date:
                date_str = current_date.strftime("%Y-%m-%d")
                count = 0
                
                # 如果当前日期有数据，则使用实际数据
                for row in daily_message_rows:
                    if row.date.strftime("%Y-%m-%d") == date_str:
                        count = row.count
                        break
                
                daily_message_count.append({
                    "date": date_str,
                    "count": count
                })
                
                current_date += timedelta(days=1)
            
            # 获取最活跃的插件
            top_plugins_query = select(
                Plugin.name,
                func.count(PluginCall.id).label("call_count")
            ).join(
                PluginCall, Plugin.name == PluginCall.plugin_name
            ).group_by(
                Plugin.name
            ).order_by(
                desc("call_count")
            ).limit(5)
            
            top_plugins_result = await session.execute(top_plugins_query)
            top_plugins = [
                {
                    "name": row.name,
                    "call_count": row.call_count
                }
                for row in top_plugins_result
            ]
            
            return {
                "success": True,
                "data": {
                    "user_count": user_count,
                    "group_count": group_count,
                    "message_count": message_count,
                    "recent_message_count": recent_message_count,
                    "plugin_count": plugin_count,
                    "enabled_plugin_count": enabled_plugin_count,
                    "daily_message_count": daily_message_count,
                    "top_plugins": top_plugins
                }
            }
            
    except Exception as e:
        raise HTTPException(500, f"获取统计信息失败: {str(e)}") 