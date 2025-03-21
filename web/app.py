from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
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

# 确保能导入主项目模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入项目模块
# from utils.plugin_manager import plugin_manager
# from database.XYBotDB import XYBotDB
# from database.keyvalDB import KeyvalDB

# 读取配置
config_path = Path(__file__).resolve().parent.parent / "main_config.toml"
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

# 获取机器人状态
def get_robot_status():
    # 此处可以从主程序获取真实的机器人状态
    # 目前使用模拟数据
    # 后续可以通过共享变量或数据库获取真实状态
    robot_stat_path = Path(__file__).resolve().parent.parent / "resource" / "robot_stat.json"
    
    if os.path.exists(robot_stat_path):
        with open(robot_stat_path, "r") as f:
            robot_stat = json.load(f)
            
        return {
            "online": True,  # 假设机器人在线
            "wxid": robot_stat.get("wxid", ""),
            "nickname": "XBotV2", # 后续从真实数据获取
            "alias": "xybot",     # 后续从真实数据获取
            "plugin_count": 10,   # 后续从真实数据获取
            "message_count": 1000 # 后续从真实数据获取
        }
    else:
        return {
            "online": False,
            "wxid": "",
            "nickname": "",
            "alias": "",
            "plugin_count": 0,
            "message_count": 0
        }

# 路由定义
@app.get("/", response_class=HTMLResponse)
async def index(request: Request, username: str = Depends(get_current_username)):
    robot_status = get_robot_status()
    return templates.TemplateResponse("index.html", {"request": request, "robot": robot_status})

@app.get("/api/status")
async def get_status(username: str = Depends(get_current_username)):
    return get_robot_status()

@app.get("/plugins", response_class=HTMLResponse)
async def get_plugins_page(request: Request, username: str = Depends(get_current_username)):
    # 后续可以从plugin_manager获取真实的插件列表
    plugins = [
        {"name": "新闻插件", "id": "News", "enabled": True, "description": "获取最新新闻"},
        {"name": "签到插件", "id": "SignIn", "enabled": True, "description": "用户签到获取积分"},
        {"name": "天气插件", "id": "GetWeather", "enabled": True, "description": "查询天气信息"}
    ]
    return templates.TemplateResponse("plugins.html", {"request": request, "plugins": plugins})

@app.get("/messages", response_class=HTMLResponse)
async def get_messages_page(request: Request, username: str = Depends(get_current_username)):
    # 此处后续可以从数据库获取消息记录
    return templates.TemplateResponse("index.html", {"request": request, "robot": get_robot_status()})

@app.get("/settings", response_class=HTMLResponse)
async def get_settings_page(request: Request, username: str = Depends(get_current_username)):
    # 此处后续可以从配置文件获取设置
    return templates.TemplateResponse("index.html", {"request": request, "robot": get_robot_status()})

# API路由
@app.get("/api/plugins")
async def get_plugins_api(username: str = Depends(get_current_username)):
    # 后续可以从plugin_manager获取真实的插件列表
    plugins = [
        {"name": "新闻插件", "id": "News", "enabled": True, "description": "获取最新新闻"},
        {"name": "签到插件", "id": "SignIn", "enabled": True, "description": "用户签到获取积分"},
        {"name": "天气插件", "id": "GetWeather", "enabled": True, "description": "查询天气信息"}
    ]
    return {"plugins": plugins}

@app.post("/api/plugins/{plugin_id}/toggle")
async def toggle_plugin(plugin_id: str, username: str = Depends(get_current_username)):
    # 后续实现真实的插件启用/禁用逻辑
    return {"success": True, "message": f"插件 {plugin_id} 状态已切换"}

@app.get("/api/plugins/{plugin_id}/config")
async def get_plugin_config(plugin_id: str, username: str = Depends(get_current_username)):
    # 后续实现真实的获取插件配置逻辑
    example_config = {
        "enable": True,
        "command": ["新闻", "新闻速递"]
    }
    return {"success": True, "config": example_config}

@app.post("/api/plugins/{plugin_id}/config")
async def save_plugin_config(plugin_id: str, username: str = Depends(get_current_username)):
    # 后续实现真实的保存插件配置逻辑
    return {"success": True, "message": "配置已保存"}

# 主函数
def start_web_server():
    host = web_config.get("host", "0.0.0.0")
    port = web_config.get("port", 8080)
    debug = web_config.get("debug", False)
    
    uvicorn.run("web.app:app", host=host, port=port, reload=debug)

if __name__ == "__main__":
    start_web_server() 