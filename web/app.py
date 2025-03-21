﻿from fastapi import FastAPI, Request, Depends, HTTPException, Form, Body
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

# 配置logger
logger = logging

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
from utils.config_utils import load_toml_config, save_toml_config

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

# 微信登录页面路由
@app.get("/wechat_login", response_class=HTMLResponse)
async def wechat_login(request: Request, username: str = Depends(get_current_username)):
    """微信登录页面"""
    try:
        # 获取系统信息
        system_info = get_system_info()
        
        # 获取微信登录状态
        client = WechatAPIClient(host="localhost", port=9000)
        login_status = await client.get_login_status()
        
        # 获取登录二维码（如果未登录）
        qrcode_url = None
        if not login_status.get("is_logged_in", False):
            try:
                # 使用正确的方法获取登录二维码
                device_name = LoginMixin.create_device_name()
                device_id = LoginMixin.create_device_id()
                uuid, qrcode_base64 = await client.get_qr_code(device_name, device_id)
                qrcode_url = f"data:image/png;base64,{qrcode_base64}" if qrcode_base64 else None
            except Exception as qr_err:
                logger.error(f"获取登录二维码失败: {str(qr_err)}")
                qrcode_url = None
        
        return templates.TemplateResponse(
            "wechat_login.html",
            {
                "request": request,
                "admin_name": username,
                "system_info": system_info,
                "login_status": login_status,
                "qrcode_url": qrcode_url
            }
        )
    except Exception as e:
        logger.error(f"微信登录页面加载失败: {str(e)}")
        logger.error(traceback.format_exc())
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "admin_name": username,
                "error": "加载微信登录页面失败",
                "message": str(e),
                "error_details": traceback.format_exc(),
                "status_code": 500
            }
        )

# 插件管理页面路由
@app.get("/plugins", response_class=HTMLResponse)
async def plugins_page(request: Request, username: str = Depends(get_current_username)):
    """插件管理页面"""
    try:
        # 获取插件列表
        plugins = []
        plugin_error_msg = None
        
        try:
            # 导入插件管理器
            logger.debug("尝试导入插件管理器")
            from utils.plugin_manager import get_plugin_manager
            
            # 获取插件管理器实例
            logger.debug("尝试获取插件管理器实例")
            plugin_manager = get_plugin_manager()
            
            if plugin_manager is None:
                logger.error("插件管理器实例为空")
                plugin_error_msg = "插件管理器实例为空，请检查系统配置"
            else:
                # 获取插件列表
                logger.debug("尝试获取插件列表")
                plugins = plugin_manager.get_plugin_list()
                logger.debug(f"获取到 {len(plugins)} 个插件")
        except ImportError as import_err:
            logger.error(f"导入插件管理器失败: {str(import_err)}")
            plugin_error_msg = f"导入插件管理模块失败: {str(import_err)}"
        except AttributeError as attr_err:
            logger.error(f"插件管理器缺少必要方法: {str(attr_err)}")
            plugin_error_msg = f"插件管理器接口错误: {str(attr_err)}"
        except Exception as plugin_err:
            logger.error(f"获取插件列表失败: {str(plugin_err)}")
            logger.error(traceback.format_exc())
            plugin_error_msg = f"获取插件列表时发生错误: {str(plugin_err)}"
        
        return templates.TemplateResponse(
            "plugins.html",
            {
                "request": request,
                "admin_name": username,
                "plugins": plugins,
                "plugin_error_msg": plugin_error_msg
            }
        )
    except Exception as e:
        logger.error(f"插件页面加载失败: {str(e)}")
        logger.error(traceback.format_exc())
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "admin_name": username,
                "error": "加载插件页面失败",
                "message": str(e),
                "error_details": traceback.format_exc(),
                "status_code": 500
            }
        )

# 日志页面路由
@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request, username: str = Depends(get_current_username)):
    """日志页面"""
    try:
        # 获取日志文件列表
        logs_dir = Path("logs")
        log_files = []
        if logs_dir.exists():
            log_files = sorted([f.name for f in logs_dir.glob("*.log")], reverse=True)
        
        # 读取最新的日志文件内容
        logs = []
        if log_files:
            latest_log = logs_dir / log_files[0]
            try:
                with open(latest_log, "r", encoding="utf-8") as f:
                    # 读取最后100行
                    lines = f.readlines()[-100:]
                    for line in lines:
                        # 解析日志行
                        parts = line.strip().split(" | ", 2)
                        if len(parts) >= 3:
                            timestamp, level, message = parts
                            logs.append({
                                "timestamp": timestamp,
                                "level": level.strip(),
                                "message": message.strip()
                            })
            except Exception as log_err:
                logger.error(f"读取日志文件失败: {str(log_err)}")
        
        return templates.TemplateResponse(
            "logs.html",
            {
                "request": request,
                "admin_name": username,
                "logs": logs,
                "log_files": log_files
            }
        )
    except Exception as e:
        logger.error(f"日志页面加载失败: {str(e)}")
        logger.error(traceback.format_exc())
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "admin_name": username,
                "error": "加载日志页面失败",
                "message": str(e),
                "error_details": traceback.format_exc(),
                "status_code": 500
            }
        )

# 设置页面路由
@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, username: str = Depends(get_current_username)):
    """设置页面"""
    try:
        # 读取配置文件
        config_path = Path("main_config.toml")
        config = load_toml_config(config_path)
        
        return templates.TemplateResponse(
            "settings.html",
            {
                "request": request,
                "admin_name": username,
                "config": config
            }
        )
    except Exception as e:
        logger.error(f"设置页面加载失败: {str(e)}")
        logger.error(traceback.format_exc())
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "admin_name": username,
                "error": "加载设置页面失败",
                "message": str(e),
                "error_details": traceback.format_exc(),
                "status_code": 500
            }
        )

# 保存设置路由
@app.post("/save_settings")
async def save_settings(request: Request, username: str = Depends(get_current_username)):
    """保存设置"""
    try:
        form_data = await request.form()
        
        # 读取原配置
        config_path = Path("main_config.toml")
        config = load_toml_config(config_path)
        
        # 更新配置
        # 示例：更新Web接口设置
        if "web_port" in form_data:
            config["WebInterface"]["port"] = int(form_data["web_port"])
        if "web_host" in form_data:
            config["WebInterface"]["host"] = form_data["web_host"]
        if "admin_username" in form_data:
            config["WebInterface"]["username"] = form_data["admin_username"]
        if "admin_password" in form_data and form_data["admin_password"]:
            config["WebInterface"]["password"] = form_data["admin_password"]
        
        # 更新其他配置...
        
        # 保存配置
        save_toml_config(config_path, config)
        
        # 重定向回设置页面
        return RedirectResponse(url="/settings?success=1", status_code=303)
    except Exception as e:
        logger.error(f"保存设置失败: {str(e)}")
        logger.error(traceback.format_exc())
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "admin_name": username,
                "error": "保存设置失败",
                "message": str(e),
                "error_details": traceback.format_exc(),
                "status_code": 500
            }
        )

# 为bot_core.py模块提供的启动函数
def start_web(host='0.0.0.0', port=8080, debug=False, admin_username="admin", admin_password="admin123", minimal_mode=False):
    """
    启动Web服务器
    
    Args:
        host (str): 监听的主机地址
        port (int): 监听的端口
        debug (bool): 是否启用调试模式
        admin_username (str): 管理员用户名
        admin_password (str): 管理员密码
        minimal_mode (bool): 是否为最小模式运行
    """
    # 初始化
    setup_templates_and_static()
    
    # 启动Web服务器
    uvicorn.run(
        app, 
        host=host, 
        port=port, 
        log_level="debug" if debug else "info"
    )

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

# API路由部分
@app.get("/api/wechat/status", response_class=JSONResponse)
async def api_wechat_status(request: Request, username: str = Depends(get_current_username)):
    """获取微信登录状态"""
    try:
        # 正常模式，尝试获取真实数据
        client = WechatAPIClient(host="localhost", port=9000)
        login_status = await client.get_login_status()
        
        return JSONResponse({
            "success": True,
            "is_logged_in": login_status.get("is_logged_in", False),
            "nickname": login_status.get("nickname", ""),
            "wxid": login_status.get("wxid", ""),
            "login_time": login_status.get("login_time", 0),
            "device_type": login_status.get("device_type", ""),
            "is_simulated": False
        })
    except Exception as e:
        logger.error(f"获取微信状态失败: {str(e)}")
        logger.error(traceback.format_exc())
        
        # 出错时也提供基本响应，防止UI崩溃
        return JSONResponse({
            "success": False,
            "is_logged_in": False,
            "nickname": "连接错误",
            "wxid": "",
            "login_time": 0,
            "device_type": "Unknown",
            "error": str(e),
            "message": "获取微信状态失败，请检查服务是否正常运行"
        })

@app.post("/api/wechat/logout", response_class=JSONResponse)
async def api_wechat_logout(request: Request, username: str = Depends(get_current_username)):
    """退出微信登录"""
    try:
        client = WechatAPIClient(host="localhost", port=9000)
        success = await client.log_out()
        
        return JSONResponse({
            "success": success,
            "message": "已成功退出微信登录" if success else "退出微信登录失败"
        })
    except Exception as e:
        logger.error(f"退出微信登录失败: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse({
            "success": False,
            "message": str(e)
        })

@app.get("/api/logs", response_class=JSONResponse)
async def api_logs(
    request: Request, 
    username: str = Depends(get_current_username),
    limit: int = 100,
    level: str = "",
    search: str = ""
):
    """获取日志API"""
    try:
        # 日志目录优先级：/app/logs, /var/log/xbotv2, ./logs
        potential_log_dirs = [
            Path("/app/logs"),
            Path("/var/log/xbotv2"),
            Path("logs")
        ]
        
        # 获取日志文件列表
        log_files = []
        logs_dir = None
        
        # 尝试每个可能的目录
        for dir_path in potential_log_dirs:
            logger.debug(f"尝试查找日志目录: {dir_path}")
            if dir_path.exists() and dir_path.is_dir():
                logs_dir = dir_path
                log_files = sorted([f.name for f in dir_path.glob("*.log")], reverse=True)
                if log_files:
                    logger.debug(f"找到日志文件: {len(log_files)}个, 在目录: {logs_dir}")
                    break
        
        if not logs_dir or not log_files:
            logger.warning("未找到任何日志文件")
            return JSONResponse({
                "success": True,
                "logs": [],
                "message": "未找到日志文件"
            })
        
        # 读取最新的日志文件内容
        logs = []
        if log_files:
            latest_log = logs_dir / log_files[0]
            logger.debug(f"读取最新日志文件: {latest_log}")
            try:
                # 检查文件大小，过大时采用不同策略
                file_size = latest_log.stat().st_size
                logger.debug(f"日志文件大小: {file_size} 字节")
                
                # 大文件使用tail方式读取最后部分
                if file_size > 1024 * 1024 * 10:  # 大于10MB
                    logger.debug("日志文件较大，使用逆序读取方式")
                    with open(latest_log, "rb") as f:
                        # 从末尾开始读取最后约200KB数据
                        chunk_size = min(file_size, 1024 * 200)
                        f.seek(max(0, file_size - chunk_size))
                        last_lines = f.read().decode('utf-8', errors='replace').splitlines()
                        
                        # 保留完整行
                        if file_size > chunk_size:
                            last_lines = last_lines[1:]  # 去掉可能不完整的第一行
                        
                        # 逆序处理
                        for line in reversed(last_lines):
                            # 如果已经达到限制，停止读取
                            if len(logs) >= limit:
                                break
                                
                            # 尝试解析日志行
                            try:
                                # 处理多种可能的日志格式
                                if " | " in line:
                                    parts = line.strip().split(" | ", 2)
                                    if len(parts) >= 3:
                                        timestamp, log_level, message = parts
                                elif "] [" in line:
                                    # 匹配类似[2023-04-01 12:34:56] [INFO] 消息内容的格式
                                    match = re.search(r'\[(.*?)\]\s*\[(.*?)\](.*)', line)
                                    if match:
                                        timestamp, log_level, message = match.groups()
                                    else:
                                        continue
                                else:
                                    # 其他无法识别的格式，简单分割
                                    timestamp = ""
                                    log_level = "INFO"
                                    message = line.strip()
                                
                                # 级别过滤
                                if level and level.upper() != log_level.strip().upper():
                                    continue
                                    
                                # 关键词过滤
                                if search and search.lower() not in message.lower():
                                    continue
                                    
                                logs.append({
                                    "timestamp": timestamp,
                                    "level": log_level.strip(),
                                    "message": message.strip()
                                })
                            except Exception as parse_err:
                                logger.debug(f"解析日志行失败: {parse_err}, 行内容: {line[:100]}...")
                                continue
                else:
                    # 对于小文件，直接读取全部内容
                    logger.debug("日志文件较小，直接读取全部内容")
                    with open(latest_log, "r", encoding="utf-8", errors='replace') as f:
                        lines = f.readlines()
                        # 从末尾开始读取
                        for line in reversed(lines):
                            # 如果已经达到限制，停止读取
                            if len(logs) >= limit:
                                break
                                
                            # 尝试解析日志行
                            try:
                                # 处理多种可能的日志格式
                                if " | " in line:
                                    parts = line.strip().split(" | ", 2)
                                    if len(parts) >= 3:
                                        timestamp, log_level, message = parts
                                    else:
                                        continue
                                elif "] [" in line:
                                    # 匹配类似[2023-04-01 12:34:56] [INFO] 消息内容的格式
                                    match = re.search(r'\[(.*?)\]\s*\[(.*?)\](.*)', line)
                                    if match:
                                        timestamp, log_level, message = match.groups()
                                    else:
                                        continue
                                else:
                                    # 其他无法识别的格式，简单分割
                                    timestamp = ""
                                    log_level = "INFO"
                                    message = line.strip()
                                
                                # 级别过滤
                                if level and level.upper() != log_level.strip().upper():
                                    continue
                                    
                                # 关键词过滤
                                if search and search.lower() not in message.lower():
                                    continue
                                    
                                logs.append({
                                    "timestamp": timestamp,
                                    "level": log_level.strip(),
                                    "message": message.strip()
                                })
                            except Exception as parse_err:
                                logger.debug(f"解析日志行失败: {parse_err}, 行内容: {line[:100]}...")
                                continue
            except Exception as log_err:
                logger.error(f"读取日志文件失败: {str(log_err)}")
                logger.error(traceback.format_exc())
        
        return JSONResponse({
            "success": True,
            "logs": logs,
            "file": log_files[0] if log_files else None
        })
    except Exception as e:
        logger.error(f"获取日志失败: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse({
            "success": False,
            "message": str(e)
        })

@app.get("/api/logs/download")
async def download_logs(request: Request, username: str = Depends(get_current_username)):
    """下载日志文件"""
    try:
        # 使用相同的日志目录优先级
        potential_log_dirs = [
            Path("/app/logs"),
            Path("/var/log/xbotv2"),
            Path("logs")
        ]
        
        # 获取日志文件列表
        log_files = []
        logs_dir = None
        
        # 尝试每个可能的目录
        for dir_path in potential_log_dirs:
            logger.debug(f"尝试查找日志目录(下载): {dir_path}")
            if dir_path.exists() and dir_path.is_dir():
                logs_dir = dir_path
                log_files = sorted([f.name for f in dir_path.glob("*.log")], reverse=True)
                if log_files:
                    logger.debug(f"找到日志文件(下载): {len(log_files)}个, 在目录: {logs_dir}")
                    break
        
        if not logs_dir or not log_files:
            logger.warning("未找到任何日志文件")
            raise HTTPException(status_code=404, detail="未找到日志文件")
        
        # 返回最新的日志文件
        latest_log = logs_dir / log_files[0]
        
        # 检查文件是否存在和可读
        if not latest_log.exists():
            logger.error(f"日志文件不存在: {latest_log}")
            raise HTTPException(status_code=404, detail="日志文件不存在")
            
        try:
            return FileResponse(
                path=latest_log,
                filename=log_files[0],
                media_type="text/plain"
            )
        except Exception as file_err:
            logger.error(f"返回日志文件失败: {str(file_err)}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"读取日志文件失败: {str(file_err)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载日志失败: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# 导入WechatAPIClient
from WechatAPI.api_client import WechatAPIClient



