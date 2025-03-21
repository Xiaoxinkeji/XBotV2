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
import traceback
import glob

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

# 缓存变量定义
_logs_cache = {
    "logs": [],
    "last_update": 0,
    "cache_timeout": 5  # 缓存超时时间(秒)
}

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

# 获取二维码URL
def get_qrcode_from_logs():
    """从最新的日志文件中获取登录二维码URL"""
    logger.info("开始从日志中查找二维码URL")
    
    # 尝试多个可能的日志位置
    possible_log_dirs = [
        Path(PROJECT_ROOT) / "logs",
        Path(PROJECT_ROOT) / "log",
        Path(PROJECT_ROOT),
        Path("/var/log/xbotv2"),
        Path("/logs"),
        Path(".")
    ]
    
    log_files = []
    
    # 记录搜索目录
    search_info = "搜索日志目录: "
    for log_dir in possible_log_dirs:
        search_info += f"{str(log_dir)}, "
    logger.info(search_info)
    
    # 在各个可能的目录中查找日志文件
    for logs_dir in possible_log_dirs:
        if not logs_dir.exists():
            logger.info(f"日志目录不存在: {logs_dir}")
            continue
        
        # 查找多种可能的日志文件名模式
        patterns = ["XYBot_*.log", "*.log", "xbot*.log", "bot*.log", "weixin*.log", "wechat*.log"]
        for pattern in patterns:
            pattern_files = list(logs_dir.glob(pattern))
            if pattern_files:
                logger.info(f"在 {logs_dir} 中找到 {len(pattern_files)} 个匹配 {pattern} 的日志文件")
                log_files.extend(pattern_files)
    
    # 如果找不到日志文件，尝试递归查找
    if not log_files:
        logger.info("未找到日志文件，尝试递归查找")
        for logs_dir in possible_log_dirs:
            if logs_dir.exists():
                for root, _, files in os.walk(logs_dir):
                    root_path = Path(root)
                    for file in files:
                        if file.endswith('.log'):
                            log_files.append(root_path / file)
    
    # 按修改时间排序
    log_files = sorted(log_files, key=lambda x: x.stat().st_mtime if x.exists() else 0, reverse=True)
    
    if not log_files:
        logger.warning("未找到任何日志文件")
        return None
    
    # 记录找到的日志文件
    files_info = "找到的日志文件: "
    for log_file in log_files[:5]:  # 只显示前5个
        files_info += f"{log_file.name} ({log_file.stat().st_size} bytes), "
    logger.info(files_info)
    
    # 遍历所有日志文件，按照最新的优先
    for latest_log in log_files:
        if not latest_log.exists() or latest_log.stat().st_size == 0:
            continue
            
        logger.info(f"尝试从 {latest_log} 中读取二维码")
        qrcode_url = None
        
        # 从日志文件中查找包含二维码URL的行
        try:
            # 首先尝试读取文件末尾的内容（更高效）
            lines = []
            file_size = latest_log.stat().st_size
            read_size = min(file_size, 50 * 1024)  # 最多读取最后50KB
            
            with open(latest_log, "rb") as f:
                if file_size > read_size:
                    f.seek(file_size - read_size)
                chunk = f.read().decode('utf-8', errors='ignore')
                lines = chunk.splitlines()
            
            # 如果未找到，则读取整个文件
            if not lines or (len(lines) == 1 and not lines[0].strip()):
                with open(latest_log, "r", encoding="utf-8", errors='ignore') as f:
                    lines = f.readlines()
            
            # 倒序查找，因为最新的登录二维码应该在日志文件的后面
            for line in reversed(lines):
                # 记录处理的行
                line_preview = line[:100] + "..." if len(line) > 100 else line
                logger.debug(f"处理日志行: {line_preview}")
                
                # 标准的微信二维码链接
                if "https://login.weixin.qq.com/qrcode/" in line or "https://long.open.weixin.qq.com/" in line:
                    # 提取URL
                    start_index = line.find("https://")
                    if start_index != -1:
                        end_index = line.find(" ", start_index)
                        if end_index == -1:
                            end_index = len(line)
                        qrcode_url = line[start_index:end_index].strip()
                        logger.info(f"找到标准微信二维码链接: {qrcode_url}")
                        break
                
                # 新的格式: "获取到登录二维码: https://api.pwmqr.com/qrcode/create/?url=http://weixin.qq.com/x/"
                elif "获取到登录二维码:" in line or "获取到登录二维码" in line:
                    # 提取URL
                    parts = line.split("获取到登录二维码:")
                    if len(parts) == 1:  # 处理可能的空格或其他分隔符
                        parts = line.split("获取到登录二维码")
                    
                    if len(parts) > 1:
                        url_part = parts[1].strip()
                        
                        # 判断是否是生成二维码的API链接
                        if "url=" in url_part:
                            # 提取实际的微信登录URL
                            wx_url_start = url_part.find("url=") + 4
                            wx_url = url_part[wx_url_start:].strip()
                            qrcode_url = wx_url
                        else:
                            qrcode_url = url_part
                        
                        logger.info(f"找到新格式微信二维码链接: {qrcode_url}")
                        break
                
                # 其他可能的格式，如直接包含微信链接
                elif "weixin.qq.com/x/" in line or "wx.qq.com" in line:
                    # 尝试提取微信URL
                    match = re.search(r'https?://(?:weixin|wx)\.qq\.com/[^\s"\']+', line)
                    if match:
                        qrcode_url = match.group(0)
                        logger.info(f"找到微信域名二维码链接: {qrcode_url}")
                        break
            
            if qrcode_url:
                return qrcode_url
                
        except Exception as e:
            logger.error(f"读取日志文件 {latest_log} 失败: {e}")
            logger.error(traceback.format_exc())
    
    logger.warning("在所有日志文件中都未找到二维码URL")
    return None

# 获取最近日志内容
def get_recent_logs(limit=10, search=None, level=None):
    global _logs_cache
    
    # 检查缓存是否有效
    current_time = time.time()
    if (_logs_cache and 
        _logs_cache['last_update'] > current_time - _logs_cache["cache_timeout"] and
        'logs' in _logs_cache):
        logs = _logs_cache['logs']
        if search or level:
            logs = filter_logs(logs, search, level)
        return logs[:limit]
    
    logs = []
    
    # 可能的日志目录
    log_dirs = ['logs', 'log', '../logs', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')]
    
    # 添加绝对路径
    absolute_paths = ['/var/log/xbotv2', '/app/logs']
    for path in absolute_paths:
        if os.path.exists(path) and os.path.isdir(path):
            log_dirs.append(path)
    
    # 寻找日志文件
    log_files = []
    
    # 特定的日志文件名模式
    patterns = ['XYBot_*.log', '*.log']
    
    for log_dir in log_dirs:
        for pattern in patterns:
            try:
                if os.path.exists(log_dir) and os.path.isdir(log_dir):
                    pattern_path = os.path.join(log_dir, pattern)
                    matching_files = glob.glob(pattern_path)
                    if matching_files:
                        # 按修改时间排序，最新的在前
                        matching_files.sort(key=os.path.getmtime, reverse=True)
                        log_files.extend(matching_files)
            except Exception as e:
                logs.append({"time": time.strftime('%Y-%m-%d %H:%M:%S'), 
                           "level": "ERROR", 
                           "content": f"搜索日志文件时出错 {log_dir}/{pattern}: {str(e)}"})
    
    if not log_files:
        # 如果没有找到日志文件，返回提示信息
        sample_logs = []
        
        # 添加示例日志和警告
        current_time = time.strftime('%Y-%m-%d %H:%M:%S')
        sample_logs.append({"time": current_time, 
                          "level": "WARNING", 
                          "content": "未找到日志文件。请检查以下目录："})
        
        for log_dir in log_dirs:
            sample_logs.append({"time": current_time, 
                              "level": "INFO", 
                              "content": f"- {os.path.abspath(log_dir)}"})
            
        sample_logs.append({"time": current_time, 
                          "level": "INFO", 
                          "content": "使用日志模式: " + ", ".join(patterns)})
        
        sample_logs.append({"time": current_time, 
                          "level": "WARNING", 
                          "content": "请确保XYBot正在运行并生成日志文件"})
        
        # 添加示例二维码URL
        qr_time = current_time
        qr_example = f"请使用微信扫描二维码登录: https://open.weixin.qq.com/connect/qrconnect?appid=example"
        sample_logs.append({"time": qr_time, 
                          "level": "INFO", 
                          "content": qr_example})
        
        # 更新缓存
        _logs_cache = {
            'last_update': current_time,
            'logs': sample_logs,
            'cache_timeout': 5  # 添加缓存超时
        }
        
        # 返回过滤后的样本日志
        if search or level:
            return filter_logs(sample_logs, search, level)[:limit]
        return sample_logs[:limit]
    
    # 读取最新的日志文件内容
    logs = []
    
    # 最多读取前5个日志文件
    for log_file in log_files[:5]:
        try:
            # 获取文件大小
            file_size = os.path.getsize(log_file)
            
            # 从文件尾部开始读取，最多读取100KB以避免性能问题
            read_size = min(file_size, 100 * 1024)
            
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                if read_size < file_size:
                    f.seek(file_size - read_size)
                    # 跳过第一行，因为可能是不完整的
                    f.readline()
                
                # 读取剩余内容
                content = f.read()
                
                # 分割为行并处理每一行
                lines = content.splitlines()
                
                # 使用前1000行避免内存问题
                for line in lines[-1000:]:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 尝试提取时间戳、日志级别和内容
                    try:
                        # 尝试匹配 "YYYY-MM-DD HH:mm:ss | LEVEL | MESSAGE" 格式
                        parts = line.split(' | ', 2)
                        if len(parts) >= 3:
                            time_str, level, message = parts
                            logs.append({"time": time_str, "level": level, "content": message})
                        else:
                            # 尝试匹配其他常见的日志格式
                            time_match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', line)
                            level_match = re.search(r'\b(ERROR|WARNING|INFO|DEBUG|TRACE)\b', line, re.IGNORECASE)
                            
                            if time_match:
                                time_str = time_match.group(1)
                                if level_match:
                                    level = level_match.group(1)
                                    content_start = line.find(level) + len(level)
                                    content = line[content_start:].strip()
                                else:
                                    level = "INFO"
                                    content = line[time_match.end():].strip()
                                
                                logs.append({"time": time_str, "level": level, "content": content})
                            else:
                                # 无法解析格式的行作为INFO级别日志
                                logs.append({"time": time.strftime('%Y-%m-%d %H:%M:%S'), 
                                           "level": "INFO", 
                                           "content": line})
                    except Exception as e:
                        logs.append({"time": time.strftime('%Y-%m-%d %H:%M:%S'), 
                                   "level": "ERROR", 
                                   "content": f"解析日志行时出错: {str(e)}"})
        
        except Exception as e:
            # 记录文件读取错误
            logs.append({"time": time.strftime('%Y-%m-%d %H:%M:%S'), 
                       "level": "ERROR", 
                       "content": f"读取日志文件 {log_file} 时出错: {str(e)}"})
    
    # 检查是否提取到了QR码URL
    has_qr_code = False
    for log in logs:
        content = log.get("content", "")
        if "https://login.weixin.qq.com/" in content or "https://open.weixin.qq.com/" in content or "http://weixin.qq.com/x/" in content:
            has_qr_code = True
            break
    
    # 如果没有找到QR码URL，添加提示消息
    if not has_qr_code:
        logs.append({"time": time.strftime('%Y-%m-%d %H:%M:%S'), 
                   "level": "INFO", 
                   "content": "未在日志中找到微信登录二维码链接"})
    
    # 按照时间排序（如果时间格式一致）
    try:
        logs.sort(key=lambda x: x.get("time", ""), reverse=True)
    except Exception:
        # 如果排序失败，保持原始顺序
        pass
    
    # 更新缓存
    _logs_cache = {
        'last_update': time.time(),
        'logs': logs,
        'cache_timeout': 5  # 添加缓存超时
    }
    
    # 返回过滤后的日志
    if search or level:
        return filter_logs(logs, search, level)[:limit]
    return logs[:limit]

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
    """处理微信登录请求"""
    try:
        if login_method == "qrcode":
            # 原有的扫码登录逻辑
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
            # 唤醒登录逻辑
            logger.info("开始处理唤醒登录请求")
            
            # 先尝试控制机器人启动(如果未运行)
            robot_running = is_robot_running()
            logger.info(f"机器人运行状态: {'运行中' if robot_running else '未运行'}")
            
            if not robot_running:
                logger.info("机器人未运行，尝试启动")
                control_robot("start")
                # 等待机器人启动
                start_success = False
                for i in range(15):  # 增加等待时间到15秒
                    logger.info(f"等待机器人启动...第{i+1}次检查")
                    if is_robot_running():
                        start_success = True
                        logger.info("机器人已成功启动")
                        break
                    await asyncio.sleep(1)
                
                if not start_success:
                    logger.warning("机器人启动超时")
            
            # 从日志中获取二维码URL
            logger.info("尝试从日志中获取二维码URL")
            qrcode_url = get_qrcode_from_logs()
            
            if qrcode_url:
                logger.info(f"成功从日志中获取到二维码URL: {qrcode_url[:30]}...")
                # 如果找到二维码URL，使用与扫码登录相同的方式返回
                login_uuid = str(uuid.uuid4())
                return {
                    "success": True,
                    "method": "qrcode",
                    "url": qrcode_url,
                    "uuid": login_uuid,
                    "device_id": None,
                    "message": "已从日志中找到最新的登录二维码"
                }
            else:
                logger.warning("未从日志中找到二维码URL，尝试唤醒已登录的账号")
                # 如果没找到二维码URL，使用原来的唤醒登录逻辑
                if not MODULES_LOADED:
                    logger.error("模块未加载，无法继续唤醒登录")
                    return {"success": False, "message": "模块未加载，无法登录"}
                
                try:
                    # 导入WechatAPI
                    import WechatAPI
                    
                    # 创建WechatAPI客户端
                    api_config = config.get("WechatAPIServer", {})
                    client = WechatAPI.WechatAPIClient("127.0.0.1", api_config.get("port", 9000))
                    
                    # 获取设备信息
                    robot_stat_path = PROJECT_ROOT / "resource" / "robot_stat.json"
                    if os.path.exists(robot_stat_path):
                        logger.info(f"读取机器人状态文件: {robot_stat_path}")
                        try:
                            with open(robot_stat_path, "r") as f:
                                robot_stat = json.load(f)
                            
                            device_name = robot_stat.get("device_name", None)
                            device_id = robot_stat.get("device_id", None)
                            wxid = robot_stat.get("wxid", None)
                            
                            logger.info(f"机器人状态信息: device_name={device_name}, device_id={device_id}, wxid={wxid}")
                        except Exception as e:
                            logger.error(f"读取机器人状态文件失败: {e}")
                            device_name = None
                            device_id = None
                            wxid = None
                    else:
                        logger.warning(f"机器人状态文件不存在: {robot_stat_path}")
                        device_name = None
                        device_id = None
                        wxid = None
                    
                    if not wxid:
                        logger.error("无法找到wxid信息，无法唤醒登录")
                        login_uuid = str(uuid.uuid4())
                        return {
                            "success": False, 
                            "message": "无法唤醒登录，未找到wxid信息",
                            "uuid": login_uuid,
                            "need_manual": True  # 告诉前端可能需要手动输入URL
                        }
                    
                    # 尝试唤醒登录
                    logger.info(f"尝试唤醒登录，wxid={wxid}")
                    cached_info = await client.get_cached_info(wxid)
                    if cached_info:
                        logger.info(f"找到账号缓存信息: {cached_info}")
                        uuid = await client.awaken_login(wxid)
                        logger.info(f"唤醒登录成功，uuid={uuid}")
                        return {"success": True, "method": "awaken", "uuid": uuid}
                    else:
                        logger.warning(f"未找到账号 {wxid} 的缓存信息")
                        login_uuid = str(uuid.uuid4())
                        return {
                            "success": False, 
                            "message": "无法唤醒登录，账号缓存不存在",
                            "uuid": login_uuid,
                            "need_manual": True  # 告诉前端可能需要手动输入URL
                        }
                except Exception as e:
                    logger.error(f"唤醒登录过程中出现异常: {e}")
                    logger.error(traceback.format_exc())
                    login_uuid = str(uuid.uuid4())
                    return {
                        "success": False, 
                        "message": f"唤醒登录失败: {str(e)}",
                        "uuid": login_uuid,
                        "need_manual": True  # 告诉前端可能需要手动输入URL
                    }
        
        return {"success": False, "message": "不支持的登录方式"}
    except Exception as e:
        logger.error(f"登录请求异常: {e}")
        logger.error(traceback.format_exc())
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

@app.get("/api/logs")
async def get_logs_api(limit: int = 10, search: str = None, level: str = None, username: str = Depends(get_current_username)):
    """获取最近的日志接口"""
    try:
        # 确保日志目录存在
        logs_dir = Path(PROJECT_ROOT) / "logs"
        if not logs_dir.exists():
            logs_dir.mkdir(exist_ok=True)
            logger.info(f"创建日志目录: {logs_dir}")
            # 创建一个初始日志文件，以便前端可以看到一些内容
            with open(logs_dir / "XYBot_init.log", "w", encoding="utf-8") as f:
                f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | INFO | 初始化日志文件\n")
                f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | INFO | 获取到登录二维码: http://weixin.qq.com/x/oudYJBEvV_gnGKNpZ5gF\n")
        
        # 检查日志文件数量，如果超过20个，则保留最新的10个
        try:
            manage_log_files(logs_dir)
        except Exception as e:
            logger.warning(f"管理日志文件时出错: {e}")
            
        logs = get_recent_logs(limit)
        
        # 根据搜索条件过滤日志
        if search or level:
            logs = filter_logs(logs, search, level)
            
        logger.info(f"API获取到 {len(logs)} 条日志")
        return {"success": True, "logs": logs}
    except Exception as e:
        logger.error(f"获取日志失败: {e}")
        logger.error(traceback.format_exc())
        return {"success": False, "message": f"获取日志失败: {str(e)}"}

def filter_logs(logs, search=None, level=None):
    """根据搜索条件过滤日志"""
    filtered_logs = logs
    
    # 按日志级别过滤
    if level:
        filtered_logs = [log for log in filtered_logs if log.get("level", "").upper() == level.upper()]
    
    # 按关键词搜索
    if search:
        filtered_logs = [log for log in filtered_logs if search.lower() in log.get("content", "").lower()]
    
    return filtered_logs

def manage_log_files(logs_dir, max_files=20, keep_files=10):
    """管理日志文件数量，防止磁盘空间耗尽"""
    try:
        log_files = list(logs_dir.glob("*.log"))
        if len(log_files) > max_files:
            # 按修改时间排序
            log_files.sort(key=lambda x: x.stat().st_mtime)
            # 删除较旧的文件，保留最新的keep_files个
            for old_file in log_files[:-keep_files]:
                try:
                    old_file.unlink()
                    logger.info(f"已删除旧日志文件: {old_file}")
                except Exception as e:
                    logger.warning(f"删除旧日志文件时出错: {e}")
    except Exception as e:
        logger.error(f"管理日志文件时出错: {e}")
        raise

# 主函数
def start_web_server():
    host = web_config.get("host", "0.0.0.0")
    port = web_config.get("port", 8080)
    debug = web_config.get("debug", False)
    
    uvicorn.run("web.app:app", host=host, port=port, reload=debug)

if __name__ == "__main__":
    start_web_server() 