from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
import os
import tomllib

# 导入项目内部模块
from utils.plugin_manager import plugin_manager
from WechatAPI import WechatAPIClient

router = APIRouter()

@router.get("/")
async def get_all_plugins():
    """获取所有插件信息"""
    try:
        plugins = plugin_manager.get_plugin_info()
        return {
            "success": True,
            "data": plugins
        }
    except Exception as e:
        raise HTTPException(500, f"获取插件信息失败: {str(e)}")

@router.get("/{plugin_name}")
async def get_plugin_detail(plugin_name: str):
    """获取特定插件的详细信息"""
    plugin_info = plugin_manager.get_plugin_info(plugin_name)
    if not plugin_info:
        raise HTTPException(404, f"插件 {plugin_name} 不存在")
    
    # 获取插件配置文件
    config_path = f"plugins/{plugin_name}/config.toml"
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "rb") as f:
                config = tomllib.load(f)
        except Exception as e:
            config = {"error": f"配置文件加载失败: {str(e)}"}
    
    return {
        "success": True,
        "data": {
            "info": plugin_info,
            "config": config
        }
    }

@router.post("/{plugin_name}/toggle")
async def toggle_plugin(plugin_name: str, background_tasks: BackgroundTasks):
    """启用或禁用插件"""
    try:
        if plugin_name not in plugin_manager.plugins:
            raise HTTPException(404, f"插件 {plugin_name} 不存在")
        
        # 获取当前状态
        current_state = plugin_manager.plugins[plugin_name].enabled
        
        # 在后台任务中执行启用/禁用操作
        if current_state:
            # 使用background_tasks避免阻塞
            background_tasks.add_task(plugin_manager.disable_plugin, plugin_name)
        else:
            # 假设bot是全局对象
            from bot_core import bot_core
            background_tasks.add_task(plugin_manager.enable_plugin, bot_core.bot, plugin_name)
        
        return {
            "success": True,
            "data": {
                "plugin": plugin_name,
                "new_state": not current_state,
                "message": f"插件 {plugin_name} 状态切换中..."
            }
        }
    except Exception as e:
        raise HTTPException(500, f"操作失败: {str(e)}") 