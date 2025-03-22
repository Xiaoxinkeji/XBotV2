from fastapi import FastAPI, Request, Depends, HTTPException, Form, Body
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.middleware.sessions import SessionMiddleware
import uvicorn

# 确保Body导入可用
from fastapi import Body as FastAPIBody

import json
import logging
import platform
import psutil
import os
import sys
import time
import traceback
import secrets
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import re
import math

# 获取目录结构
FILE_DIR = os.path.dirname(os.path.abspath(__file__))

# 检测项目根目录
if os.path.basename(FILE_DIR) == "web":
    BASE_DIR = os.path.dirname(FILE_DIR)
else:
    BASE_DIR = FILE_DIR

# 验证是否真的是项目根目录
if not (os.path.exists(os.path.join(BASE_DIR, "main.py")) or 
        os.path.exists(os.path.join(BASE_DIR, "main_config.toml")) or
        os.path.exists(os.path.join(BASE_DIR, "utils"))):
    # 尝试再往上一级查找
    potential_base = os.path.dirname(BASE_DIR)
    if (os.path.exists(os.path.join(potential_base, "main.py")) or 
        os.path.exists(os.path.join(potential_base, "main_config.toml")) or
        os.path.exists(os.path.join(potential_base, "utils"))):
        BASE_DIR = potential_base

# 添加项目根目录到sys.path
sys.path.insert(0, BASE_DIR)

# 导入配置工具
from utils.config_utils import load_toml_config

# 创建FastAPI应用
app = FastAPI()

# 设置静态文件目录
app.mount("/static", StaticFiles(directory=os.path.join(FILE_DIR, "static")), name="static")

# 设置模板引擎
templates = Jinja2Templates(directory=os.path.join(FILE_DIR, "templates"))

# 添加会话中间件
# 会话有效期24小时
app.add_middleware(
    SessionMiddleware,
    secret_key=secrets.token_urlsafe(32),
    max_age=86400  # 24小时
)

# 确保必要的目录结构存在
def ensure_directories():
    """确保必要的目录结构存在"""
    # 确保logs目录存在
    logs_dir = os.path.join(BASE_DIR, "logs")
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # 确保resource目录存在
    resource_dir = os.path.join(BASE_DIR, "resource")
    if not os.path.exists(resource_dir):
        os.makedirs(resource_dir)
    
    # 确保database目录存在
    database_dir = os.path.join(BASE_DIR, "database")
    if not os.path.exists(database_dir):
        os.makedirs(database_dir)
    
    # 确保plugins目录存在
    plugins_dir = os.path.join(BASE_DIR, "plugins")
    if not os.path.exists(plugins_dir):
        os.makedirs(plugins_dir)
    
    # 确保静态资源目录存在
    static_dir = os.path.join(FILE_DIR, "static")
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
        
        # 创建基本的CSS文件
        css_dir = os.path.join(static_dir, "css")
        if not os.path.exists(css_dir):
            os.makedirs(css_dir)
            with open(os.path.join(css_dir, "style.css"), "w") as f:
                f.write("""
:root {
    --primary: #0d6efd;
    --secondary: #6c757d;
    --success: #198754;
    --danger: #dc3545;
    --warning: #ffc107;
    --info: #0dcaf0;
    --light: #f8f9fa;
    --dark: #212529;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin: 0;
    padding: 0;
    background-color: #f5f7fa;
}
                """)
        
        # 创建基本的JS文件
        js_dir = os.path.join(static_dir, "js")
        if not os.path.exists(js_dir):
            os.makedirs(js_dir)
            with open(os.path.join(js_dir, "main.js"), "w") as f:
                f.write("""
// 页面加载完成后执行
document.addEventListener("DOMContentLoaded", function() {
    console.log("XBotV2 Web管理界面已加载");
});
                """)

# HTTP异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """处理HTTP异常"""
    # 处理401未授权错误 - 重定向到登录页面
    if exc.status_code == 401:
        return RedirectResponse(url="/login")
    
    # 处理其他HTTP异常
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "success": False}
        )
    
    # 尝试获取用户名（如果已登录）
    admin_name = None
    try:
        if hasattr(request, "session") and "username" in request.session:
            admin_name = request.session.get("username")
    except Exception:
        pass
    
    # 为非API请求返回友好的错误页面
    return templates.TemplateResponse(
        "error.html", 
        {
            "request": request,
            "status_code": exc.status_code,
            "error": f"HTTP {exc.status_code}",
            "message": exc.detail,
            "admin_name": admin_name
        }
    )

# 通用异常处理器
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理所有其他类型的异常"""
    error_id = str(uuid.uuid4())
    error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 记录错误详情
    error_details = f"时间: {error_time}\n"
    error_details += f"错误ID: {error_id}\n"
    error_details += f"URL: {request.url}\n"
    error_details += f"方法: {request.method}\n"
    error_details += f"异常类型: {type(exc).__name__}\n"
    error_details += f"异常详情: {str(exc)}\n"
    error_details += f"堆栈跟踪:\n{traceback.format_exc()}"
    
    # 记录到日志
    logging.error(f"未捕获的异常: {error_id}\n{error_details}")
    
    # 如果是API请求，返回JSON响应
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={
                "detail": "服务器内部错误",
                "error_id": error_id,
                "success": False
            }
        )
    
    # 尝试获取用户名（如果已登录）
    admin_name = None
    try:
        if hasattr(request, "session") and "username" in request.session:
            admin_name = request.session.get("username")
    except Exception:
        pass
    
    # 非API请求返回错误页面
    return templates.TemplateResponse(
        "error.html", 
        {
            "request": request,
            "status_code": 500,
            "error": "服务器内部错误",
            "message": f"系统发生了内部错误。请联系管理员并提供以下错误ID: {error_id}",
            "error_details": error_details if os.environ.get("DEBUG") == "true" else None,
            "admin_name": admin_name
        }
    )

# 初始化应用
def setup_templates_and_static():
    """初始化模板和静态文件"""
    ensure_directories()

# 获取运行时间
def get_uptime():
    """获取系统运行时间"""
    try:
        if platform.system() == "Windows":
            uptime_seconds = time.time() - psutil.boot_time()
        else:
            uptime_seconds = time.time() - psutil.boot_time()
        
        # 将秒转换为可读格式
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        
        if days > 0:
            return f"{days}天 {hours}小时 {minutes}分钟"
        elif hours > 0:
            return f"{hours}小时 {minutes}分钟"
        else:
            return f"{minutes}分钟"
    except Exception as e:
        logging.error(f"获取系统运行时间失败: {e}")
        return "Unknown"

# 获取系统信息
def get_system_info():
    """获取系统信息"""
    try:
        info = {
            "os": f"{platform.system()} {platform.release()}",
            "python": platform.python_version(),
            "uptime": get_uptime(),
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent
        }
        return info
    except Exception as e:
        logging.error(f"获取系统信息失败: {e}")
        return {"os": "Unknown", "uptime": "Unknown"}

# 获取当前用户名
def get_current_username(request: Request):
    """获取当前登录的用户名"""
    if "username" not in request.session:
        raise HTTPException(status_code=401, detail="未授权访问")
    
    return request.session.get("username")

# 首页路由
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, username: str = Depends(get_current_username)):
    """首页"""
    # 获取系统信息
    system_info = get_system_info()
    
    # 获取用户信息
    user_info = {"nickname": "未知", "wxid": "未知"}
    try:
        profile_path = os.path.join(BASE_DIR, "resource", "profile.json")
        if os.path.exists(profile_path):
            with open(profile_path, "r", encoding="utf-8") as f:
                profile_data = json.load(f)
                user_info = {
                    "nickname": profile_data.get("nickname", "未知"),
                    "wxid": profile_data.get("wxid", "未知"),
                    "avatar_url": profile_data.get("avatar_url", "")
                }
    except Exception as e:
        logging.error(f"获取用户信息失败: {e}")
    
    # 获取最后活跃时间
    last_active_time = "未知"
    try:
        # 尝试读取上次活跃时间
        last_active_path = os.path.join(BASE_DIR, "resource", "last_active.txt")
        if os.path.exists(last_active_path):
            with open(last_active_path, "r") as f:
                timestamp = float(f.read().strip())
                dt = datetime.fromtimestamp(timestamp)
                last_active_time = dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logging.error(f"获取最后活跃时间失败: {e}")
    
    # 构建状态信息
    content = f"""
    ### 服务器信息
    
    - 系统: {system_info.get('os', 'Unknown')}
    
    - 运行时间: {system_info.get('uptime', 'Unknown')}
    
    ### 最后在线信息
    
    - 昵称: {user_info.get('nickname', 'Unknown')}
    
    - 微信ID: {user_info.get('wxid', 'Unknown')}
    
    - 最后活跃时间: {last_active_time}
    """
    
    # 是否发送离线通知
    try:
        # 获取机器人状态
        robot_status = "offline"  # 默认离线
        
        # 传递数据到模板
        return templates.TemplateResponse(
            "index.html", 
            {
                "request": request,
                "admin_name": username,
                "robot_status": robot_status,
                "system_info": system_info,
                "user_info": user_info,
                "last_active_time": last_active_time,
                "messages": []  # 可以添加消息通知
            }
        )
    except Exception as e:
        logging.error(f"渲染首页失败: {e}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

# 登录页面路由
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, message: str = None):
    """登录页面"""
    # 如果已登录，重定向到首页
    if "username" in request.session:
        return RedirectResponse(url="/")
    
    return templates.TemplateResponse(
        "user_login.html", 
        {
            "request": request,
            "message": message
        }
    )

# 认证路由
@app.post("/auth")
async def authenticate(request: Request, 
                     username: str = Form(...), 
                     password: str = Form(...)):
    """处理登录认证"""
    try:
        # 加载配置
        config_path = os.path.join(BASE_DIR, "main_config.toml")
        config = load_toml_config(config_path)
        
        # 获取配置的用户名和密码
        web_config = config.get("WebInterface", {})
        admin_username = web_config.get("username", "admin")
        admin_password = web_config.get("password", "admin123")
        
        # 验证用户名和密码
        if username == admin_username and password == admin_password:
            # 设置会话
            request.session["username"] = username
            return RedirectResponse(url="/", status_code=303)
        else:
            return templates.TemplateResponse(
                "user_login.html", 
                {
                    "request": request,
                    "message": "用户名或密码错误"
                }
            )
    except Exception as e:
        logging.error(f"认证失败: {e}")
        return templates.TemplateResponse(
            "user_login.html", 
            {
                "request": request,
                "message": f"登录处理出错: {str(e)}"
            }
        )

# 登出路由
@app.get("/logout")
async def logout(request: Request):
    """登出操作"""
    # 清除会话
    request.session.clear()
    return RedirectResponse(url="/login")

# 启动Web服务器
def start_web_server():
    """启动Web服务器"""
    # 加载配置
    config_path = os.path.join(BASE_DIR, "main_config.toml")
    config = load_toml_config(config_path)
    
    # 获取配置
    web_config = config.get("WebInterface", {})
    port = web_config.get("port", 8080)
    host = web_config.get("host", "0.0.0.0")
    debug = web_config.get("debug", False)
    
    # 初始化
    setup_templates_and_static()
    
    # 启动服务器
    uvicorn.run(
        "web.app:app",
        host=host,
        port=port,
        reload=debug,
        log_level="debug" if debug else "info"
    )

# 当直接运行此文件时
if __name__ == "__main__":
    start_web_server() 



