from fastapi import FastAPI, Request, HTTPException, Depends, status, Form, Body
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import asyncio
import os
import tomllib
import secrets
from pathlib import Path
import sys
import json
from typing import List, Dict, Any, Optional
import importlib
import shutil
import toml
import psutil
import subprocess
import platform
from datetime import datetime
import httpx
import uuid
import logging
import time
import re
import importlib.util
import git
from pydantic import BaseModel

# 确保能导入主项目模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入项目模块
try:
    from utils.plugin_manager import plugin_manager
    from database.keyvalDB import KeyvalDB
    MODULES_LOADED = True
except ImportError:
    MODULES_LOADED = False

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("web")

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

# 读取配置
config_path = PROJECT_ROOT / "main_config.toml"
with open(config_path, "rb") as f:
    config = tomllib.load(f)

web_config = config.get("WebInterface", {})
auth_enabled = True
auth_username = web_config.get("username", "admin")
auth_password = web_config.get("password", "admin123")

app = FastAPI(title="XBotV2 Web管理",
              description="XBotV2微信机器人管理界面",
              version="0.1.0")

# 设置静态文件和模板
templates = Jinja2Templates(directory="web/templates")
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# 安全认证
security = HTTPBasic()

# Pydantic模型定义
class LoginRequest(BaseModel):
    login_method: str

class LoginCheckResponse(BaseModel):
    success: bool
    logged_in: bool
    message: Optional[str] = None
    wxid: Optional[str] = None
    nickname: Optional[str] = None
    alias: Optional[str] = None

class Message(BaseModel):
    type: str
    content: str

class Plugin(BaseModel):
    id: str
    name: str
    enabled: bool
    description: Optional[str] = None
    version: Optional[str] = None
    author: Optional[str] = None

class StatusResponse(BaseModel):
    online: bool
    wxid: str
    nickname: str
    alias: str
    plugin_count: int
    message_count: int

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    if auth_enabled:
        correct_username = secrets.compare_digest(credentials.username, auth_username)
        correct_password = secrets.compare_digest(credentials.password, auth_password)
        if not (correct_username and correct_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Basic"},
            )
    return credentials.username

# 检查机器人是否运行
def is_robot_running():
    # 检查机器人进程是否在运行
    if platform.system() == "Windows":
        # Windows平台
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] and "python" in proc.info['name'].lower():
                try:
                    cmdline = " ".join(proc.cmdline())
                    if "bot_core.py" in cmdline or "main.py" in cmdline:
                        return True, proc.pid
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
    else:
        # Linux/macOS平台
        for proc in psutil.process_iter(['pid', 'cmdline']):
            try:
                cmdline = " ".join(proc.info['cmdline'] or [])
                if ("bot_core.py" in cmdline or "main.py" in cmdline) and "web/app.py" not in cmdline:
                    return True, proc.pid
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    return False, None

# 获取机器人状态
def get_robot_status():
    # 通过检查机器人进程和运行时状态确定在线状态
    robot_stat_path = PROJECT_ROOT / "resource" / "robot_stat.json"
    robot_online, _ = is_robot_running()
    wxid = ""
    nickname = ""
    alias = ""
    plugin_count = 0
    message_count = 0
    
    # 检查机器人状态
    if os.path.exists(robot_stat_path):
        with open(robot_stat_path, "r") as f:
            robot_stat = json.load(f)
        wxid = robot_stat.get("wxid", "")
        
        # 通过keyvalDB检查登录状态
        if MODULES_LOADED and robot_online:
            try:
                # 获取已加载插件数量
                if plugin_manager:
                    # 检查plugin_manager是否有loaded_plugins属性
                    if hasattr(plugin_manager, 'loaded_plugins'):
                        plugin_count = len(plugin_manager.loaded_plugins)
                    elif hasattr(plugin_manager, 'plugins'):
                        plugin_count = len(plugin_manager.plugins)
                    else:
                        # 使用文件系统计算活跃插件数量
                        plugin_count = len([p for p in get_plugins() if p['enabled']])
                
                # 从数据库获取消息数量
                # 此处可以添加消息统计逻辑
            except Exception as e:
                logger.error(f"获取机器人状态出错: {e}")
                # 发生错误时使用文件系统方法获取插件数量
                try:
                    plugin_count = len([p for p in get_plugins() if p['enabled']])
                except:
                    plugin_count = 0
    
    # 获取机器人个人信息
    profile_path = PROJECT_ROOT / "resource" / "profile.json"
    if os.path.exists(profile_path):
        try:
            with open(profile_path, "r") as f:
                profile = json.load(f)
            nickname = profile.get("nickname", "")
            alias = profile.get("alias", "")
        except:
            pass
            
    return {
        "online": robot_online,
        "wxid": wxid,
        "nickname": nickname or "XYBot",
        "alias": alias or "xybot",
        "plugin_count": plugin_count,
        "message_count": message_count
    }

# 获取所有插件列表
def get_plugins():
    plugins = []
    plugins_dir = PROJECT_ROOT / "plugins"
    
    # 如果插件目录不存在，创建一个空目录
    if not plugins_dir.exists():
        plugins_dir.mkdir(parents=True, exist_ok=True)
        return plugins
    
    # 获取禁用插件列表
    disabled_plugins = config.get("XYBot", {}).get("disabled-plugins", [])
    
    # 获取所有插件目录
    all_plugin_dirs = [d for d in plugins_dir.iterdir() if d.is_dir()]
    
    for plugin_dir in all_plugin_dirs:
        plugin_id = plugin_dir.name
        
        # 跳过以点开头的目录和__pycache__目录
        if plugin_id.startswith('.') or plugin_id == '__pycache__':
            continue
        
        plugin_info = {
            "id": plugin_id,
            "name": plugin_id,
            "enabled": plugin_id not in disabled_plugins,
            "description": "无描述",
            "version": "未知",
            "author": "未知"
        }
        
        # 尝试读取插件配置获取信息
        config_path = plugin_dir / "config.toml"
        if config_path.exists():
            try:
                with open(config_path, "rb") as f:
                    plugin_config = tomllib.load(f)
                
                # 从配置中提取信息
                for section in plugin_config.values():
                    if isinstance(section, dict):
                        if "description" in section:
                            plugin_info["description"] = section["description"]
                        if "version" in section:
                            plugin_info["version"] = section["version"]
                        if "author" in section:
                            plugin_info["author"] = section["author"]
            except:
                pass
        
        # 检查插件README.md
        readme_path = plugin_dir / "README.md"
        if readme_path.exists():
            plugin_info["readme"] = True
        
        plugins.append(plugin_info)
    
    return plugins

# 获取插件配置
def get_plugin_config(plugin_id: str):
    plugin_config_path = PROJECT_ROOT / "plugins" / plugin_id / "config.toml"
    if not plugin_config_path.exists():
        return None
    
    try:
        with open(plugin_config_path, "rb") as f:
            config_data = tomllib.load(f)
        return config_data
    except:
        return None

# 安装插件
async def install_plugin(install_type: str, **kwargs):
    plugins_dir = PROJECT_ROOT / "plugins"
    
    # 确保插件目录存在
    if not plugins_dir.exists():
        plugins_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        if install_type == "git":
            git_url = kwargs.get("git_url")
            git_branch = kwargs.get("git_branch", "main")
            
            if not git_url:
                return {"success": False, "message": "未提供Git仓库URL"}
            
            # 从URL获取插件名称
            plugin_name = git_url.rstrip("/").split("/")[-1]
            if plugin_name.endswith(".git"):
                plugin_name = plugin_name[:-4]
            
            plugin_dir = plugins_dir / plugin_name
            
            # 检查目标目录是否已存在
            if plugin_dir.exists():
                return {"success": False, "message": f"插件目录 {plugin_name} 已存在"}
            
            # 克隆Git仓库
            subprocess.run(
                ["git", "clone", "-b", git_branch, git_url, str(plugin_dir)],
                check=True
            )
            
            # 检查配置文件
            plugin_config = get_plugin_config(plugin_name)
            if not plugin_config:
                # 创建默认配置
                default_config = {
                    "plugin": {
                        "name": plugin_name,
                        "description": "从Git仓库安装的插件",
                        "version": "1.0.0",
                        "author": "未知"
                    }
                }
                
                with open(plugin_dir / "config.toml", "w") as f:
                    toml.dump(default_config, f)
            
            return {
                "success": True, 
                "message": f"插件 {plugin_name} 已安装",
                "plugin": {
                    "id": plugin_name,
                    "name": plugin_name,
                    "enabled": True
                }
            }
            
        elif install_type == "local":
            local_path = kwargs.get("local_path")
            
            if not local_path:
                return {"success": False, "message": "未提供本地路径"}
            
            local_path = Path(local_path)
            if not local_path.exists():
                return {"success": False, "message": f"路径 {local_path} 不存在"}
            
            if not local_path.is_dir():
                return {"success": False, "message": f"{local_path} 不是目录"}
            
            # 获取插件名称
            plugin_name = local_path.name
            plugin_dir = plugins_dir / plugin_name
            
            # 检查目标目录是否已存在
            if plugin_dir.exists():
                return {"success": False, "message": f"插件目录 {plugin_name} 已存在"}
            
            # 复制文件
            shutil.copytree(local_path, plugin_dir)
            
            # 检查配置文件
            plugin_config = get_plugin_config(plugin_name)
            if not plugin_config:
                # 创建默认配置
                default_config = {
                    "plugin": {
                        "name": plugin_name,
                        "description": "从本地安装的插件",
                        "version": "1.0.0",
                        "author": "未知"
                    }
                }
                
                with open(plugin_dir / "config.toml", "w") as f:
                    toml.dump(default_config, f)
            
            return {
                "success": True, 
                "message": f"插件 {plugin_name} 已安装",
                "plugin": {
                    "id": plugin_name,
                    "name": plugin_name,
                    "enabled": True
                }
            }
            
        elif install_type == "zip":
            zip_url = kwargs.get("zip_url")
            
            if not zip_url:
                return {"success": False, "message": "未提供ZIP文件URL"}
            
            # 从URL获取插件名称
            plugin_name = zip_url.rstrip("/").split("/")[-1]
            if plugin_name.endswith(".zip"):
                plugin_name = plugin_name[:-4]
            
            plugin_dir = plugins_dir / plugin_name
            
            # 检查目标目录是否已存在
            if plugin_dir.exists():
                return {"success": False, "message": f"插件目录 {plugin_name} 已存在"}
            
            # 创建临时目录
            import tempfile
            temp_dir = tempfile.mkdtemp()
            temp_zip = os.path.join(temp_dir, "plugin.zip")
            
            # 下载ZIP文件
            async with httpx.AsyncClient() as client:
                response = await client.get(zip_url)
                if response.status_code != 200:
                    return {"success": False, "message": f"下载ZIP文件失败: {response.status_code}"}
                
                with open(temp_zip, "wb") as f:
                    f.write(response.content)
            
            # 解压ZIP文件
            import zipfile
            with zipfile.ZipFile(temp_zip, "r") as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # 找到主目录
            extracted_dirs = [d for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))]
            if len(extracted_dirs) == 1:
                # 只有一个目录，使用该目录
                main_dir = os.path.join(temp_dir, extracted_dirs[0])
            else:
                # 有多个目录，找到包含__init__.py的目录
                main_dir = None
                for d in extracted_dirs:
                    if os.path.exists(os.path.join(temp_dir, d, "__init__.py")):
                        main_dir = os.path.join(temp_dir, d)
                        break
                
                # 如果没有找到，使用temp_dir
                if not main_dir:
                    main_dir = temp_dir
            
            # 复制文件
            shutil.copytree(main_dir, plugin_dir)
            
            # 检查配置文件
            plugin_config = get_plugin_config(plugin_name)
            if not plugin_config:
                # 创建默认配置
                default_config = {
                    "plugin": {
                        "name": plugin_name,
                        "description": "从ZIP文件安装的插件",
                        "version": "1.0.0",
                        "author": "未知"
                    }
                }
                
                with open(plugin_dir / "config.toml", "w") as f:
                    toml.dump(default_config, f)
            
            # 清理临时文件
            shutil.rmtree(temp_dir)
            
            return {
                "success": True, 
                "message": f"插件 {plugin_name} 已安装",
                "plugin": {
                    "id": plugin_name,
                    "name": plugin_name,
                    "enabled": True
                }
            }
            
        else:
            return {"success": False, "message": f"不支持的安装类型: {install_type}"}
            
    except Exception as e:
        logger.error(f"安装插件失败: {e}")
        return {"success": False, "message": f"安装插件失败: {str(e)}"}

# 删除插件
def delete_plugin(plugin_id: str, delete_files: bool = False):
    # 读取配置
    with open(config_path, "rb") as f:
        current_config = tomllib.load(f)
    
    disabled_plugins = current_config.get("XYBot", {}).get("disabled-plugins", [])
    
    # 检查插件是否存在
    plugin_dir = PROJECT_ROOT / "plugins" / plugin_id
    if not plugin_dir.is_dir():
        return {"success": False, "message": f"插件 {plugin_id} 不存在"}
    
    try:
        # 如果在禁用列表中，移除
        if plugin_id in disabled_plugins:
            disabled_plugins.remove(plugin_id)
            current_config["XYBot"]["disabled-plugins"] = disabled_plugins
            
            with open(config_path, "w") as f:
                toml.dump(current_config, f)
        
        # 如果需要删除文件
        if delete_files:
            shutil.rmtree(plugin_dir)
        
        return {"success": True, "message": f"插件 {plugin_id} 已删除"}
    except Exception as e:
        logger.error(f"删除插件失败: {e}")
        return {"success": False, "message": f"删除插件失败: {str(e)}"}

# 更新插件
async def update_plugin(plugin_id: str):
    plugin_dir = PROJECT_ROOT / "plugins" / plugin_id
    
    # 检查插件是否存在
    if not plugin_dir.is_dir():
        return {"success": False, "message": f"插件 {plugin_id} 不存在"}
    
    # 检查是否为Git仓库
    git_dir = plugin_dir / ".git"
    if not git_dir.is_dir():
        return {"success": False, "message": f"插件 {plugin_id} 不是Git仓库"}
    
    try:
        # 获取当前分支
        result = subprocess.run(
            ["git", "-C", str(plugin_dir), "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=True
        )
        current_branch = result.stdout.strip()
        
        # 拉取最新代码
        subprocess.run(
            ["git", "-C", str(plugin_dir), "pull", "origin", current_branch],
            check=True
        )
        
        return {"success": True, "message": f"插件 {plugin_id} 已更新"}
    except Exception as e:
        logger.error(f"更新插件失败: {e}")
        return {"success": False, "message": f"更新插件失败: {str(e)}"}

# 控制机器人
def control_robot(action: str):
    if action not in ["start", "stop", "restart"]:
        return {"success": False, "message": f"不支持的操作: {action}"}
    
    try:
        if action == "start":
            # 检查是否已经在运行
            running, _ = is_robot_running()
            if running:
                return {"success": False, "message": "机器人已在运行"}
            
            # 启动机器人
            if platform.system() == "Windows":
                subprocess.Popen(["python", "main.py"], cwd=str(PROJECT_ROOT))
            else:
                subprocess.Popen(["python3", "main.py"], cwd=str(PROJECT_ROOT))
            
            # 等待启动
            time.sleep(2)
            
            # 检查是否成功启动
            running, _ = is_robot_running()
            if running:
                return {"success": True, "message": "机器人已启动"}
            else:
                return {"success": False, "message": "启动机器人失败"}
                
        elif action == "stop":
            # 检查是否在运行
            running, pid = is_robot_running()
            if not running:
                return {"success": False, "message": "机器人未在运行"}
            
            # 终止进程
            process = psutil.Process(pid)
            process.terminate()
            
            # 等待进程终止
            gone, still_alive = psutil.wait_procs([process], timeout=3)
            if still_alive:
                # 强制终止
                for p in still_alive:
                    p.kill()
            
            return {"success": True, "message": "机器人已停止"}
            
        elif action == "restart":
            # 先停止
            running, pid = is_robot_running()
            if running:
                process = psutil.Process(pid)
                process.terminate()
                gone, still_alive = psutil.wait_procs([process], timeout=3)
                if still_alive:
                    for p in still_alive:
                        p.kill()
            
            # 等待完全停止
            time.sleep(2)
            
            # 启动
            if platform.system() == "Windows":
                subprocess.Popen(["python", "main.py"], cwd=str(PROJECT_ROOT))
            else:
                subprocess.Popen(["python3", "main.py"], cwd=str(PROJECT_ROOT))
            
            # 等待启动
            time.sleep(2)
            
            # 检查是否成功启动
            running, _ = is_robot_running()
            if running:
                return {"success": True, "message": "机器人已重启"}
            else:
                return {"success": False, "message": "重启机器人失败"}
    
    except Exception as e:
        logger.error(f"控制机器人失败: {e}")
        return {"success": False, "message": f"控制机器人失败: {str(e)}"}

# 路由定义
@app.get("/", response_class=HTMLResponse)
async def index(request: Request, username: str = Depends(get_current_username)):
    robot_status = get_robot_status()
    return templates.TemplateResponse("index.html", {"request": request, "robot": robot_status})

@app.get("/api/status")
async def get_status_api(username: str = Depends(get_current_username)):
    return get_robot_status()

@app.get("/plugins", response_class=HTMLResponse)
async def get_plugins_page(request: Request, username: str = Depends(get_current_username)):
    plugins = get_plugins()
    return templates.TemplateResponse("plugins.html", {"request": request, "plugins": plugins})

@app.get("/plugin_config", response_class=HTMLResponse)
async def get_plugin_config_page(request: Request, id: str, username: str = Depends(get_current_username)):
    # 验证插件是否存在
    plugin_dir = PROJECT_ROOT / "plugins" / id
    if not plugin_dir.is_dir():
        return RedirectResponse(url="/plugins")
    
    # 获取插件信息
    plugins = get_plugins()
    plugin = next((p for p in plugins if p["id"] == id), None)
    
    if not plugin:
        return RedirectResponse(url="/plugins")
    
    # 获取插件配置
    config_data = get_plugin_config(id) or {}
    
    return templates.TemplateResponse("plugin_config.html", {
        "request": request, 
        "plugin": plugin,
        "config": config_data
    })

@app.get("/messages", response_class=HTMLResponse)
async def get_messages_page(request: Request, username: str = Depends(get_current_username)):
    # 此处后续可以从数据库获取消息记录
    return templates.TemplateResponse("messages.html", {"request": request, "robot": get_robot_status()})

@app.get("/settings", response_class=HTMLResponse)
async def get_settings_page(request: Request, username: str = Depends(get_current_username)):
    # 加载系统设置
    with open(config_path, "rb") as f:
        system_config = tomllib.load(f)
    
    return templates.TemplateResponse("settings.html", {"request": request, "robot": get_robot_status(), "config": system_config})

@app.get("/login", response_class=HTMLResponse)
async def get_login_page(request: Request, username: str = Depends(get_current_username)):
    return templates.TemplateResponse("login.html", {"request": request, "robot": get_robot_status()})

# API路由
@app.get("/api/plugins")
async def get_plugins_api(username: str = Depends(get_current_username)):
    plugins = get_plugins()
    return {"success": True, "plugins": plugins}

@app.post("/api/plugins/{plugin_id}/toggle")
async def toggle_plugin(plugin_id: str, username: str = Depends(get_current_username)):
    # 读取配置
    with open(config_path, "rb") as f:
        current_config = tomllib.load(f)
    
    disabled_plugins = current_config.get("XYBot", {}).get("disabled-plugins", [])
    
    # 检查插件是否存在
    plugin_dir = PROJECT_ROOT / "plugins" / plugin_id
    if not plugin_dir.is_dir():
        return {"success": False, "message": f"插件 {plugin_id} 不存在"}
    
    # 切换状态
    if plugin_id in disabled_plugins:
        disabled_plugins.remove(plugin_id)
        new_status = True  # 启用
    else:
        disabled_plugins.append(plugin_id)
        new_status = False  # 禁用
    
    # 更新配置
    current_config["XYBot"]["disabled-plugins"] = disabled_plugins
    
    try:
        # 保存配置
        with open(config_path, "w") as f:
            toml.dump(current_config, f)
        
        return {"success": True, "message": f"插件 {plugin_id} 已{'启用' if new_status else '禁用'}", "enabled": new_status}
    except Exception as e:
        return {"success": False, "message": f"切换插件状态失败: {str(e)}"}

@app.get("/api/plugins/{plugin_id}/config")
async def get_plugin_config_api(plugin_id: str, username: str = Depends(get_current_username)):
    # 获取插件信息
    plugins = get_plugins()
    plugin = next((p for p in plugins if p["id"] == plugin_id), None)
    
    if not plugin:
        return {"success": False, "message": f"插件 {plugin_id} 不存在"}
    
    # 获取配置
    config_data = get_plugin_config(plugin_id) or {}
    
    return {
        "success": True, 
        "name": plugin["name"], 
        "enabled": plugin["enabled"], 
        "config": config_data
    }

@app.post("/api/plugins/{plugin_id}/config")
async def save_plugin_config(
    plugin_id: str, 
    config_data: Dict[str, Any] = Body(...),
    username: str = Depends(get_current_username)
):
    plugin_config_path = PROJECT_ROOT / "plugins" / plugin_id / "config.toml"
    
    # 检查插件目录
    plugin_dir = PROJECT_ROOT / "plugins" / plugin_id
    if not plugin_dir.is_dir():
        return {"success": False, "message": f"插件 {plugin_id} 不存在"}
    
    # 启用/禁用插件
    enabled = config_data.pop("enabled", True)
    with open(config_path, "rb") as f:
        main_config = tomllib.load(f)
    
    disabled_plugins = main_config.get("XYBot", {}).get("disabled-plugins", [])
    
    if not enabled and plugin_id not in disabled_plugins:
        disabled_plugins.append(plugin_id)
    elif enabled and plugin_id in disabled_plugins:
        disabled_plugins.remove(plugin_id)
    
    main_config["XYBot"]["disabled-plugins"] = disabled_plugins
    
    try:
        # 保存主配置
        with open(config_path, "w") as f:
            toml.dump(main_config, f)
        
        # 保存插件配置
        with open(plugin_config_path, "w") as f:
            toml.dump(config_data["config"], f)
        
        return {"success": True, "message": "配置已保存"}
    except Exception as e:
        return {"success": False, "message": f"保存配置失败: {str(e)}"}

@app.post("/api/plugins/install")
async def install_plugin_api(
    install_type: str = Form(...),
    git_url: Optional[str] = Form(None),
    git_branch: Optional[str] = Form(None),
    local_path: Optional[str] = Form(None),
    zip_url: Optional[str] = Form(None),
    username: str = Depends(get_current_username)
):
    kwargs = {}
    if git_url:
        kwargs["git_url"] = git_url
    if git_branch:
        kwargs["git_branch"] = git_branch
    if local_path:
        kwargs["local_path"] = local_path
    if zip_url:
        kwargs["zip_url"] = zip_url
    
    result = await install_plugin(install_type, **kwargs)
    return result

@app.post("/api/plugins/{plugin_id}/delete")
async def delete_plugin_api(
    plugin_id: str,
    delete_files: bool = Body(False),
    username: str = Depends(get_current_username)
):
    return delete_plugin(plugin_id, delete_files)

@app.post("/api/plugins/{plugin_id}/update")
async def update_plugin_api(plugin_id: str, username: str = Depends(get_current_username)):
    return await update_plugin(plugin_id)

@app.post("/api/robot/control/{action}")
async def control_robot_api(action: str, username: str = Depends(get_current_username)):
    return control_robot(action)

@app.post("/api/wechat/login")
async def wechat_login(login_method: str = Form(...), username: str = Depends(get_current_username)):
    try:
        if not MODULES_LOADED:
            return {"success": False, "message": "模块未加载，无法登录"}
        
        # 导入WechatAPI
        import WechatAPI
        
        # 创建WechatAPI客户端
        api_config = config.get("WechatAPIServer", {})
        client = WechatAPI.WechatAPIClient("127.0.0.1", api_config.get("port", 9000))
        
        # 获取设备信息
        robot_stat_path = PROJECT_ROOT / "resource" / "robot_stat.json"
        if os.path.exists(robot_stat_path):
            with open(robot_stat_path, "r") as f:
                robot_stat = json.load(f)
            
            device_name = robot_stat.get("device_name", None)
            device_id = robot_stat.get("device_id", None)
            wxid = robot_stat.get("wxid", None)
        else:
            device_name = None
            device_id = None
            wxid = None
        
        if login_method == "qrcode":
            # 创建必要的设备信息
            if not device_name:
                device_name = client.create_device_name()
            if not device_id:
                device_id = client.create_device_id()
            
            # 获取二维码
            uuid, url = await client.get_qr_code(device_id=device_id, device_name=device_name, print_qr=True)
            
            return {
                "success": True, 
                "method": "qrcode", 
                "uuid": uuid, 
                "url": url,
                "device_id": device_id,
                "device_name": device_name
            }
        
        elif login_method == "awaken":
            if not wxid:
                return {"success": False, "message": "无法唤醒登录，未找到wxid信息"}
            
            # 尝试唤醒登录
            if await client.get_cached_info(wxid):
                uuid = await client.awaken_login(wxid)
                return {"success": True, "method": "awaken", "uuid": uuid}
            else:
                return {"success": False, "message": "无法唤醒登录，账号缓存不存在"}
        
        else:
            return {"success": False, "message": "不支持的登录方式"}
            
    except Exception as e:
        return {"success": False, "message": f"登录请求失败: {str(e)}"}

@app.get("/api/wechat/check_login/{uuid}")
async def check_login_status(uuid: str, device_id: Optional[str] = None, username: str = Depends(get_current_username)):
    try:
        if not MODULES_LOADED:
            return {"success": False, "message": "模块未加载，无法检查登录状态"}
        
        # 导入WechatAPI
        import WechatAPI
        
        # 创建WechatAPI客户端
        api_config = config.get("WechatAPIServer", {})
        client = WechatAPI.WechatAPIClient("127.0.0.1", api_config.get("port", 9000))
        
        # 检查登录状态
        status, data = await client.check_login_uuid(uuid, device_id=device_id)
        
        if status:
            # 获取登录账号信息
            client.wxid = data.get("acctSectResp").get("userName")
            client.nickname = data.get("acctSectResp").get("nickName")
            client.alias = data.get("acctSectResp").get("alias")
            client.phone = data.get("acctSectResp").get("bindMobile")
            
            # 保存登录信息
            robot_stat_path = PROJECT_ROOT / "resource" / "robot_stat.json"
            robot_stat = {
                "wxid": client.wxid,
                "device_name": device_id,  # 这里可能有问题，应该是device_name
                "device_id": device_id
            }
            
            with open(robot_stat_path, "w") as f:
                json.dump(robot_stat, f)
            
            # 保存个人信息
            profile_path = PROJECT_ROOT / "resource" / "profile.json"
            profile = {
                "wxid": client.wxid,
                "nickname": client.nickname,
                "alias": client.alias,
                "phone": client.phone
            }
            
            with open(profile_path, "w") as f:
                json.dump(profile, f)
            
            return {
                "success": True, 
                "logged_in": True,
                "wxid": client.wxid,
                "nickname": client.nickname,
                "alias": client.alias
            }
        else:
            return {"success": True, "logged_in": False, "message": data}
            
    except Exception as e:
        return {"success": False, "message": f"检查登录状态失败: {str(e)}"}

@app.post("/api/settings/save")
async def save_settings(config_data: Dict[str, Any] = Body(...), username: str = Depends(get_current_username)):
    try:
        # 保存配置到main_config.toml
        with open(config_path, "w") as f:
            tomllib.dump(config_data, f)
        
        return {"success": True, "message": "配置已保存"}
    except Exception as e:
        logger.error(f"保存配置失败: {e}")
        return {"success": False, "message": f"保存配置失败: {str(e)}"}

# 主函数
def start_web_server():
    host = web_config.get("host", "0.0.0.0")
    port = web_config.get("port", 8080)
    debug = web_config.get("debug", False)
    
    uvicorn.run("web.app:app", host=host, port=port, reload=debug)

if __name__ == "__main__":
    start_web_server() 