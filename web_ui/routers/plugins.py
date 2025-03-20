from fastapi import APIRouter, HTTPException, BackgroundTasks, Body, UploadFile, File, Query
from typing import List, Dict, Any, Optional
import os
import tomllib
import tomli_w
import shutil
import zipfile
from pathlib import Path

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

@router.post("/{plugin_name}/config")
async def update_plugin_config(plugin_name: str, config: Dict[str, Any] = Body(...)):
    """更新插件配置文件"""
    try:
        if plugin_name not in plugin_manager.plugins:
            raise HTTPException(404, f"插件 {plugin_name} 不存在")
            
        config_path = f"plugins/{plugin_name}/config.toml"
        
        # 备份原配置
        if os.path.exists(config_path):
            shutil.copy(config_path, f"{config_path}.bak")
            
        # 写入新配置
        with open(config_path, "wb") as f:
            tomli_w.dump(config, f)
            
        return {
            "success": True,
            "message": f"插件 {plugin_name} 配置已更新"
        }
    except Exception as e:
        if os.path.exists(f"{config_path}.bak"):
            shutil.move(f"{config_path}.bak", config_path)
        raise HTTPException(500, f"更新配置失败: {str(e)}")

@router.get("/categories")
async def get_plugin_categories():
    """获取插件分类"""
    categories = {}
    for name, plugin in plugin_manager.plugins.items():
        category = getattr(plugin, "category", "未分类")
        if category not in categories:
            categories[category] = []
        categories[category].append(name)
    
    return {
        "success": True,
        "data": categories
    }

@router.post("/upload")
async def upload_plugin(plugin_file: UploadFile = File(...)):
    """上传并安装新插件"""
    try:
        # 创建临时目录
        temp_dir = Path("temp_plugins")
        temp_dir.mkdir(exist_ok=True)
        
        # 保存上传的文件
        file_path = temp_dir / plugin_file.filename
        with open(file_path, "wb") as f:
            shutil.copyfileobj(plugin_file.file, f)
        
        # 解压插件
        plugin_name = None
        if file_path.suffix == ".zip":
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # 获取插件名称 (假设zip内的顶级目录是插件名)
                plugin_name = zip_ref.namelist()[0].split('/')[0]
                # 解压到插件目录
                zip_ref.extractall("plugins/")
        else:
            raise HTTPException(400, "上传的文件必须是ZIP格式")
        
        # 清理临时文件
        os.remove(file_path)
        
        return {
            "success": True,
            "data": {
                "plugin_name": plugin_name,
                "message": f"插件 {plugin_name} 上传成功，请重启机器人以加载插件"
            }
        }
    except Exception as e:
        raise HTTPException(500, f"上传插件失败: {str(e)}") 