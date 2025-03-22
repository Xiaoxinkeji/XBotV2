from fastapi import FastAPI, Request, Depends, HTTPException, Form, Body
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.middleware.sessions import SessionMiddleware
import uvicorn  # 添加缺失的uvicorn导入

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

# 改进目录结构检�?
try:
    # 获取当前文件所在目�?
    FILE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # 检测项目根目录
    # 1. 如果当前在web子目录中
    if os.path.basename(FILE_DIR) == "web":
        BASE_DIR = os.path.dirname(FILE_DIR)
    # 2. 如果当前直接在项目根目录
    else:
        BASE_DIR = FILE_DIR
    
    # 增加一个健壮性检�?- 验证是否真的是项目根目录
    # 通过检查几个关键文�?目录来判�?
    if not (os.path.exists(os.path.join(BASE_DIR, "main.py")) or 
            os.path.exists(os.path.join(BASE_DIR, "main_config.toml")) or
            os.path.exists(os.path.join(BASE_DIR, "utils"))):
        # 尝试再往上一级查�?
        potential_base = os.path.dirname(BASE_DIR)
        if (os.path.exists(os.path.join(potential_base, "main.py")) or 
            os.path.exists(os.path.join(potential_base, "main_config.toml")) or
            os.path.exists(os.path.join(potential_base, "utils"))):
            BASE_DIR = potential_base
    
    # 转换为Path对象
    PROJECT_ROOT = Path(BASE_DIR)
    
    # 记录项目根目录信�?
    print(f"项目根目�? {BASE_DIR}")
except Exception as e:
    print(f"确定项目根目录时出错: {e}")
    # 使用当前工作目录作为后备
    BASE_DIR = os.getcwd()
    PROJECT_ROOT = Path(BASE_DIR)
    print(f"使用当前工作目录作为项目根目�? {BASE_DIR}")

# 导入统一的配置工具
try:
    sys.path.append(BASE_DIR)
    from utils.config_utils import load_toml_config, save_toml_config
except ImportError:
    print("无法导入config_utils模块，尝试添加路径")
    sys.path.insert(0, str(PROJECT_ROOT))
    try:
        from utils.config_utils import load_toml_config, save_toml_config
        print("成功导入config_utils模块")
    except ImportError as e:
        print(f"导入config_utils失败: {e}")
        # 定义简单的替代函数
        def load_toml_config(path):
            print(f"使用内置的配置读取功�? {path}")
            if not os.path.exists(path):
                return {}
            try:
                import toml
                with open(path, "r", encoding="utf-8") as f:
                    return toml.load(f)
            except:
                try:
                    import tomli
                    with open(path, "rb") as f:
                        return tomli.load(f)
                except:
                    return {}
        
        def save_toml_config(path, data):
            try:
                import toml
                with open(path, "w", encoding="utf-8") as f:
                    toml.dump(data, f)
                return True
            except:
                return False

# 定义模块加载状�?
MODULES_LOADED = False

# 配置日志
# 确保logs目录存在
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)

logger = logging.getLogger("web")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(BASE_DIR, "logs", "web.log"), encoding="utf-8")
    ]
)

# 机器人上一次状�?
_last_robot_status = {"is_online": False, "last_check_time": 0}

# 检查机器人状态变化并触发通知
def check_robot_status_change(robot_status):
    """检查机器人状态变化并触发通知"""
    global _last_robot_status
    current_is_online = robot_status.get("is_online", False)
    last_is_online = _last_robot_status.get("is_online", False)
    
    # 获取通知配置
    config = get_config()
    notification_config = config.get("Notification", {})
    enable_notification = notification_config.get("enable", False)
    pushplus_token = notification_config.get("pushplus-token", "")
    notify_online = notification_config.get("notify-online", True)
    notify_offline = notification_config.get("notify-offline", True)
    online_title = notification_config.get("online-title", "机器人已上线")
    offline_title = notification_config.get("offline-title", "机器人已掉线")
    
    # 状态发生变�?
    if current_is_online != last_is_online:
        logger.info(f"机器人状态变�? {'上线' if current_is_online else '离线'}")
        
        # 如果启用了通知且PushPlus令牌有效
        if enable_notification and pushplus_token:
            # 构建通知内容
            if current_is_online and notify_online:
                # 机器人上线通知
                system_info = get_system_info()
                user_info = robot_status.get("user_info", {})
                plugins = get_plugins()
                active_plugins = [p for p in plugins if p.get("enabled", False)]
                
                content = f"""
                ### 服务器信�?
                - 系统: {system_info.get('os', 'Unknown')}
                - 运行时间: {system_info.get('uptime', 'Unknown')}
                - CPU使用�? {system_info.get('cpu_usage', 0)}%
                - 内存使用�? {system_info.get('memory_usage', 0)}%
                
                ### 微信账号
                - 昵称: {user_info.get('nickname', 'Unknown')}
                - 微信ID: {user_info.get('wxid', 'Unknown')}
                
                ### 已激活插�?{len(active_plugins)})
                {', '.join([p.get('name', 'Unknown') for p in active_plugins])}
                """
                
                # 发送上线通知
                try:
                    send_notification(online_title, content)
                    logger.info("已发送机器人上线通知")
                except Exception as e:
                    logger.error(f"发送上线通知失败: {e}")
            
            elif not current_is_online and notify_offline:
                # 机器人离线通知
                system_info = get_system_info()
                user_info = _last_robot_status.get("user_info", {})
                last_active_time = _last_robot_status.get("last_active_time", "未知")
                
                content = f"""
                ### 服务器信�?
                - 系统: {system_info.get('os', 'Unknown')}
                - 运行时间: {system_info.get('uptime', 'Unknown')}
                
                ### 最后在线信�?
                - 昵称: {user_info.get('nickname', 'Unknown')}
                - 微信ID: {user_info.get('wxid', 'Unknown')}
                - 最后活�? {last_active_time}
                """
                
                # 发送离线通知
                try:
                    send_notification(offline_title, content)
                    logger.info("已发送机器人离线通知")
                except Exception as e:
                    logger.error(f"发送离线通知失败: {e}")
    
    # 更新上一次状�?
    _last_robot_status = robot_status
    _last_robot_status["last_check_time"] = time.time()

# 发送通知
def send_notification(title, content):
    """发送推送通知"""
    config = get_config()
    notification_config = config.get("Notification", {})
    token = notification_config.get("pushplus-token", "")
    
    if not token:
        logger.warning("未配置PushPlus令牌，无法发送通知")
        return False
    
    try:
        import requests
        url = "http://www.pushplus.plus/send"
        data = {
            "token": token,
            "title": title,
            "content": content,
            "template": "markdown"
        }
        response = requests.post(url, json=data)
        result = response.json()
        
        if result.get("code") == 200:
            return True
        else:
            logger.warning(f"PushPlus通知发送失�? {result.get('msg', '未知错误')}")
            return False
    except Exception as e:
        logger.error(f"发送通知出错: {e}")
        return False

# 获取消息统计
def get_message_stats():
    """获取消息统计信息"""
    try:
        # 假设我们有一个消息数据库，从中获取统计信�?
        # 这里简化为返回固定结构
        current_time = datetime.now()
        today = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)
        
        # 尝试从数据库获取消息统计
        try:
            # 这部分代码应该根据实际的数据库结构来编写
            # 这里只是一个示例框�?
            import sqlite3
            conn = sqlite3.connect(str(Path(BASE_DIR) / "database" / "message.db"))
            cursor = conn.cursor()
            
            # 获取今日消息数量
            cursor.execute("SELECT COUNT(*) FROM messages WHERE timestamp >= ?", (today.timestamp(),))
            today_count = cursor.fetchone()[0]
            
            # 获取昨日消息数量
            cursor.execute("SELECT COUNT(*) FROM messages WHERE timestamp >= ? AND timestamp < ?", 
                          (yesterday.timestamp(), today.timestamp()))
            yesterday_count = cursor.fetchone()[0]
            
            # 获取总消息数�?
            cursor.execute("SELECT COUNT(*) FROM messages")
            total_count = cursor.fetchone()[0]
            
            # 获取过去7天的消息数量
            seven_days_ago = today - timedelta(days=7)
            cursor.execute("SELECT COUNT(*) FROM messages WHERE timestamp >= ?", (seven_days_ago.timestamp(),))
            week_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "today": today_count,
                "yesterday": yesterday_count,
                "total": total_count,
                "week": week_count,
                "last_updated": current_time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as db_error:
            logger.warning(f"无法从数据库获取消息统计: {db_error}")
            # 如果数据库查询失败，返回默认�?
            return {
                "today": 0,
                "yesterday": 0,
                "total": 0,
                "week": 0,
                "last_updated": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "error": str(db_error)
            }
            
    except Exception as e:
        logger.error(f"获取消息统计时出�? {e}")
        return {
            "today": 0,
            "yesterday": 0,
            "total": 0,
            "week": 0,
            "error": str(e)
        }

# 确保必要的目录存�?
def ensure_directories():
    """确保必要的目录结构存�?""
    logger.info("开始检查并创建必要的目录结�?..")
    dirs = [
        PROJECT_ROOT / "logs",
        PROJECT_ROOT / "resource",
        PROJECT_ROOT / "resource" / "images",  # 添加图片资源目录
        PROJECT_ROOT / "resource" / "qrcode",  # 添加二维码目�?
        PROJECT_ROOT / "database",
        PROJECT_ROOT / "plugins",
        PROJECT_ROOT / "web" / "templates",
        PROJECT_ROOT / "web" / "static",
        PROJECT_ROOT / "web" / "static" / "css",
        PROJECT_ROOT / "web" / "static" / "js",
        PROJECT_ROOT / "web" / "static" / "img"
    ]
    
    created_count = 0
    for directory in dirs:
        if not directory.exists():
            logger.warning(f"目录不存在，尝试创建: {directory}")
            try:
                directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"成功创建目录: {directory}")
                created_count += 1
            except Exception as e:
                logger.error(f"创建目录失败 {directory}: {e}")
                logger.error(traceback.format_exc())
                
    if created_count > 0:
        logger.info(f"共创建了 {created_count} 个目�?)
    else:
        logger.info("所有必要的目录已经存在")
    
    # 确保templates目录中有必要的模板文�?
    template_dir = PROJECT_ROOT / "web" / "templates"
    if not list(template_dir.glob("*.html")):
        logger.warning("templates目录为空，可能会导致Web界面无法正常显示")
    
    # 确保static目录中有必要的静态文�?
    static_dir = PROJECT_ROOT / "web" / "static"
    css_dir = static_dir / "css"
    js_dir = static_dir / "js"
    if not list(css_dir.glob("*.css")) or not list(js_dir.glob("*.js")):
        logger.warning("静态文件目录可能缺少必要的CSS或JS文件，可能会影响Web界面的显示和功能")
    
    # 检查resource目录中的关键文件
    resource_dir = PROJECT_ROOT / "resource"
    if not (resource_dir / "robot_stat.json").exists():
        try:
            # 创建一个基本的状态文�?
            with open(resource_dir / "robot_stat.json", "w", encoding="utf-8") as f:
                json.dump({"status": "offline", "last_update": int(time.time())}, f)
            logger.info("创建了默认的robot_stat.json文件")
        except Exception as e:
            logger.error(f"创建robot_stat.json失败: {e}")
            
    return True

# 设置工作目录
ensure_directories()

# 直接读取配置以确定DEBUG模式
DEBUG = False
try:
    # 尝试读取配置文件
    config_paths = [
        Path(BASE_DIR) / "main_config.toml",  # 标准路径
        Path("main_config.toml"),            # 工作目录
        Path("..") / "main_config.toml",     # 上级目录
        Path(__file__).parent.parent / "main_config.toml"  # 相对于脚本的路径
    ]
    
    for config_path in config_paths:
        if config_path.exists():
            try:
                config = load_toml_config(config_path)
                if config and "WebInterface" in config:
                    DEBUG = config["WebInterface"].get("debug", False)
                    break
            except Exception as e:
                logger.error(f"读取配置文件失败: {e}")
except Exception as e:
    logger.error(f"确定DEBUG模式时出�? {e}")

logger.info(f"Debug模式: {'开�? if DEBUG else '关闭'}")

# 创建FastAPI应用实例
app = FastAPI(
    title="XBotV2", 
    description="微信机器人Web管理界面", 
    version="1.0.0",
    docs_url=None if not DEBUG else "/docs",
    redoc_url=None if not DEBUG else "/redoc",
)

# 会话密钥
SESSION_SECRET_KEY = secrets.token_urlsafe(32)
# 如果需要持久密钥，可以从配置中加载或存储到文件�?
try:
    session_key_file = os.path.join(BASE_DIR, "resource", "session_key.txt")
    if os.path.exists(session_key_file):
        with open(session_key_file, "r") as f:
            SESSION_SECRET_KEY = f.read().strip()
    else:
        # 创建目录(如果不存�?
        os.makedirs(os.path.dirname(session_key_file), exist_ok=True)
        # 保存密钥到文�?
        with open(session_key_file, "w") as f:
            f.write(SESSION_SECRET_KEY)
except Exception as e:
    logger.warning(f"处理会话密钥文件时出�? {e}，使用内存中的随机密�?)

# 添加异常处理程序
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """处理HTTP异常，如果是认证错误则重定向到登录页�?""
    if exc.status_code == 401:
        # 对于API路由返回JSON响应
        if request.url.path.startswith("/api/"):
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail, "success": False}
            )
        # 对于页面路由重定向到登录页面
        return RedirectResponse(url=f"/login?message={exc.detail}", status_code=303)
    
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
    
    # 为非API请求返回友好的错误页�?
    return templates.TemplateResponse(
        "error.html", 
        {
            "request": request, 
            "status_code": exc.status_code, 
            "error": f"错误 {exc.status_code}", 
            "message": exc.detail,
            "error_details": traceback.format_exc() if DEBUG else None,
            "admin_name": admin_name
        },
        status_code=exc.status_code
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理所有其他异�?""
    # 记录异常
    logger.error(f"未处理的异常: {exc}")
    logger.error(traceback.format_exc())
    
    # 对于API路由
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={"detail": "内部服务器错�?, "message": str(exc), "success": False}
        )
    
    # 尝试获取用户名（如果已登录）
    admin_name = None
    try:
        if hasattr(request, "session") and "username" in request.session:
            admin_name = request.session.get("username")
    except Exception:
        pass
    
    # 对于常规页面请求
    return templates.TemplateResponse(
        "error.html", 
        {
            "request": request, 
            "status_code": 500, 
            "error": "内部服务器错�?, 
            "message": str(exc),
            "error_details": traceback.format_exc() if DEBUG else None,
            "admin_name": admin_name
        },
        status_code=500
    )

# 添加会话中间�?
app.add_middleware(
    SessionMiddleware, 
    secret_key=SESSION_SECRET_KEY,
    max_age=86400,  # 会话有效�?4小时
)

# 确保目录结构存在
ensure_directories()

# 初始化模板和静态文件目录
def setup_templates_and_static():
    """初始化模板和静态文件目录"""
    # 模板目录处理
    templates_paths = [
        PROJECT_ROOT / "web" / "templates",  # 标准路径
        PROJECT_ROOT / "templates",          # 备选路径
        Path(__file__).parent / "templates", # 相对于当前脚本的路径
        Path("templates")                    # 相对于工作目录的路径
    ]
    
    templates_path = None
    for path in templates_paths:
        if path.exists() and path.is_dir():
            logger.info(f"找到模板目录: {path}")
            templates_path = path
            break
    
    if not templates_path:
        # 创建一个模板目录作为备用
        logger.error("未找到任何可用的模板目录，创建一个默认目录")
        templates_path = PROJECT_ROOT / "web" / "templates"
        templates_path.mkdir(parents=True, exist_ok=True)
        
        # 尝试创建一个最小的模板文件以便应用仍能运行
        try:
            with open(templates_path / "fallback.html", "w", encoding="utf-8") as f:
                f.write("""<!DOCTYPE html>
<html>
<head>
    <title>XBotV2 - 系统错误</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
        h1 { color: #d9534f; }
        .info { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>XBotV2 系统错误</h1>
        <p>模板文件未找到。请确保项目安装正确，并包含所有必要的文件。</p>
        <div class="info">
            <p>可能的解决方法：</p>
            <ul>
                <li>确认项目已完整克隆/下载</li>
                <li>检查web/templates目录是否存在</li>
                <li>尝试重新启动应用</li>
            </ul>
        </div>
    </div>
</body>
</html>""")
            logger.info("已创建一个基本的模板文件")
        except Exception as e:
            logger.error(f"创建基本模板文件失败: {e}")
    
    # 静态文件目录处理
    static_paths = [
        PROJECT_ROOT / "web" / "static",   # 标准路径
        PROJECT_ROOT / "static",           # 备选路径
        Path(__file__).parent / "static",  # 相对于当前脚本的路径
        Path("static")                     # 相对于工作目录的路径
    ]
    
    static_path = None
    for path in static_paths:
        if path.exists() and path.is_dir():
            logger.info(f"找到静态文件目录: {path}")
            static_path = path
            break
    
    if not static_path:
        # 创建一个静态文件目录作为备用
        logger.error("未找到任何可用的静态文件目录，创建一个默认目录")
        static_path = PROJECT_ROOT / "web" / "static"
        static_path.mkdir(parents=True, exist_ok=True)
        css_dir = static_path / "css"
        css_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建一个基本的CSS文件
        try:
            with open(css_dir / "style.css", "w", encoding="utf-8") as f:
                f.write("""body {
    font-family: Arial, sans-serif;
    background-color: #f5f5f5;
    margin: 0;
    padding: 0;
}
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    background-color: #fff;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
}
h1, h2, h3 {
    color: #333;
}
.error {
    color: #d9534f;
    background-color: #f9f2f2;
    padding: 10px;
    border-radius: 4px;
    margin: 20px 0;
}
""")
            logger.info("已创建一个基本的CSS文件")
        except Exception as e:
            logger.error(f"创建CSS文件失败: {e}")
    
    return templates_path, static_path

# 设置模板和静态文�?
templates_path, static_path = setup_templates_and_static()
templates = Jinja2Templates(directory=str(templates_path))

# 挂载静态文件目�?
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# 获取系统运行时间的辅助函�?
def get_uptime():
    """获取系统运行时间"""
    try:
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        days, seconds = uptime.days, uptime.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{days}�?{hours}小时 {minutes}分钟"
    except Exception as e:
        logger.error(f"获取系统运行时间出错: {e}")
        return "未知"

# 配置相关函数
def get_config():
    """获取当前配置"""
    try:
        # 首先检查是否可以导入config_utils
        try:
            from utils.config_utils import load_toml_config
        except ImportError:
            logger.error("无法导入config_utils模块，可能是路径问题")
            # 尝试直接导入
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            try:
                from utils.config_utils import load_toml_config
                logger.info("通过路径调整成功导入config_utils")
            except ImportError as e:
                logger.error(f"调整路径后仍无法导入config_utils: {e}")
                return {
                    "WebInterface": {
                        "username": "admin",
                        "password": "admin123",
                        "enable": True,
                        "host": "0.0.0.0",
                        "port": 8080
                    }
                }
        
        # 尝试以不同的相对路径查找配置文件
        config_paths = [
            Path(BASE_DIR) / "main_config.toml",  # 标准路径
            Path("main_config.toml"),            # 工作目录
            Path("..") / "main_config.toml",     # 上级目录
            Path(__file__).parent.parent / "main_config.toml"  # 相对于脚本的路径
        ]
        
        config = None
        loaded_path = None
        
        for config_path in config_paths:
            logger.info(f"尝试读取配置文件: {config_path}")
            if config_path.exists():
                logger.info(f"找到配置文件: {config_path}")
                loaded_path = config_path
                
                # 直接读取文件内容用于日志记录和调�?
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        file_content = f.read()
                        logger.debug(f"配置文件内容预览: {file_content[:100]}...")
                except Exception as read_error:
                    logger.error(f"直接读取配置文件失败: {read_error}")
                
                # 使用统一配置工具加载TOML
                config = load_toml_config(config_path)
                if config:
                    logger.info(f"�?{config_path} 成功加载配置")
                    break
        
        # 检查配置是否正确加�?
        if not config:
            logger.error("所有配置文件路径都失败，使用默认配�?)
            config = {
                "WebInterface": {
                    "username": "admin",
                    "password": "admin123",
                    "enable": True,
                    "host": "0.0.0.0",
                    "port": 8080,
                    "debug": False
                }
            }
        else:
            logger.info(f"配置文件 {loaded_path} 加载成功，包含的部分: {list(config.keys())}")
            
            # 检查并确保WebInterface部分存在且包含必要的�?
            if "WebInterface" not in config:
                logger.warning("配置文件中缺少WebInterface部分，添加默认�?)
                config["WebInterface"] = {
                    "username": "admin",
                    "password": "admin123",
                    "enable": True,
                    "host": "0.0.0.0",
                    "port": 8080,
                    "debug": False
                }
            else:
                web_config = config["WebInterface"]
                # 确保关键配置项存�?
                if "username" not in web_config or not web_config["username"]:
                    web_config["username"] = "admin"
                if "password" not in web_config or not web_config["password"]:
                    web_config["password"] = "admin123"
                if "enable" not in web_config:
                    web_config["enable"] = True
                if "host" not in web_config:
                    web_config["host"] = "0.0.0.0"
                if "port" not in web_config:
                    web_config["port"] = 8080
                if "debug" not in web_config:
                    web_config["debug"] = False
        
        return config
        
    except Exception as e:
        logger.error(f"获取配置时出�? {e}")
        logger.error(traceback.format_exc())
        # 返回默认配置，确保应用可以继续运�?
        return {
            "WebInterface": {
                "username": "admin",
                "password": "admin123",
                "enable": True,
                "host": "0.0.0.0",
                "port": 8080,
                "debug": False
            }
        }

# 用户认证相关函数
security = HTTPBasic()

def get_current_username(request: Request):
    """获取当前用户名，如果未登录则重定向到登录页面"""
    try:
        # 检查session是否存在
        if not hasattr(request, "session"):
            logger.error("请求对象没有session属�?)
            raise HTTPException(
                status_code=401,
                detail="会话无效",
                headers={"WWW-Authenticate": "Basic"},
            )
            
        username = request.session.get("username")
        authenticated = request.session.get("authenticated", False)
        
        if not username or not authenticated:
            # 记录未认证的请求
            remote_addr = request.client.host if hasattr(request, "client") and hasattr(request.client, "host") else "unknown"
            logger.warning(f"未认证的请求尝试访问受保护的路由，来源IP：{remote_addr}")
            
            # 返回401状态码，前端可以捕获并处理
            raise HTTPException(
                status_code=401,
                detail="未认证，请先登录",
                headers={"WWW-Authenticate": "Basic"},
            )
        
        return username
    except HTTPException:
        # 重新抛出HTTP异常以便FastAPI处理
        raise
    except Exception as e:
        # 处理任何其他异常
        logger.error(f"获取当前用户名时出错: {e}")
        logger.error(traceback.format_exc())
        
        # 返回通用错误
        raise HTTPException(
            status_code=500,
            detail=f"内部服务器错�? {str(e)}",
        )

@app.post("/auth")
async def authenticate(request: Request, 
                     username: str = Form(...), 
                     password: str = Form(...)):
    """处理登录表单提交"""
    try:
        logger.info(f"用户尝试登录: {username}")
        config = get_config()
        
        # 默认凭据，以防配置文件读取失�?
        default_username = "admin"
        default_password = "admin123"
        
        # 从配置中获取用户名和密码
        if config and "WebInterface" in config:
            config_username = config["WebInterface"].get("username", default_username)
            config_password = config["WebInterface"].get("password", default_password)
        else:
            logger.warning("无法从配置中读取用户名和密码，使用默认�?)
            config_username = default_username
            config_password = default_password
            
        # 清理输入和配置�?
        username = username.strip()
        password = password.strip()
        config_username = config_username.strip()
        config_password = config_password.strip()
        
        # 详细登录日志，不记录完整密码
        logger.debug(f"输入的用户名: '{username}', 长度: {len(username)}")
        logger.debug(f"输入的密码长�? {len(password)}")
        logger.debug(f"配置的用户名: '{config_username}', 长度: {len(config_username)}")
        logger.debug(f"配置的密码长�? {len(config_password)}")
        
        # 检查凭据是否匹�?
        if username == config_username and password == config_password:
            logger.info(f"用户 {username} 登录成功")
            # 设置会话
            request.session["username"] = username
            request.session["authenticated"] = True
            request.session["login_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 重定向到首页
            return RedirectResponse(url="/", status_code=303)
        else:
            # 尝试使用默认凭据（如果用户未使用配置中的凭据�?
            if username == default_username and password == default_password and (config_username != default_username or config_password != default_password):
                logger.warning(f"用户 {username} 使用默认凭据登录成功")
                # 设置会话
                request.session["username"] = username
                request.session["authenticated"] = True
                request.session["login_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 重定向到首页，但带有警告消息
                return RedirectResponse(url="/?message=您使用了默认凭据登录，建议更改密�?, status_code=303)
            
            logger.warning(f"用户 {username} 登录失败 - 凭据不匹�?)
            if username == config_username:
                logger.debug("用户名匹配，但密码不匹配")
            
            # 登录失败，重定向回登录页�?
            return RedirectResponse(url=f"/login?message=用户名或密码不正�?, status_code=303)
    except Exception as e:
        logger.error(f"登录处理过程中出�? {e}")
        logger.error(traceback.format_exc())
        return RedirectResponse(url=f"/login?message=登录处理出错: {str(e)}", status_code=303)

# 检查机器人是否运行
def is_robot_running():
    # 检查机器人进程是否在运�?
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

# 获取系统信息
def get_system_info():
    """获取系统信息"""
    try:
        # 获取系统基本信息
        system_info = {
            "os": f"{platform.system()} {platform.release()}",
            "python_version": platform.python_version(),
            "hostname": platform.node(),
            "cpu_count": psutil.cpu_count(logical=True),
            "cpu_usage": round(psutil.cpu_percent(), 2),
            "memory_total": round(psutil.virtual_memory().total / (1024 * 1024 * 1024), 2),  # GB
            "memory_used": round(psutil.virtual_memory().used / (1024 * 1024 * 1024), 2),  # GB
            "memory_usage": round(psutil.virtual_memory().percent, 2),
            "disk_total": round(psutil.disk_usage('/').total / (1024 * 1024 * 1024), 2),  # GB
            "disk_used": round(psutil.disk_usage('/').used / (1024 * 1024 * 1024), 2),  # GB
            "disk_usage": round(psutil.disk_usage('/').percent, 2),
            "uptime": get_uptime(),
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return system_info
    except Exception as e:
        logger.error(f"获取系统信息时出�? {e}")
        return {
            "os": f"{platform.system()} {platform.release()}",
            "error": str(e),
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

# 获取机器人状�?
def get_robot_status():
    """获取机器人状�?""
    try:
        # 这里应该是实际检查机器人状态的代码
        # 为简化，这里返回一个示例状�?
        return {
            "online": True,
            "wxid": "wxid_example",
            "nickname": "XBot机器�?,
            "alias": "XBot",
            "plugin_count": 5,
            "message_count": 100
        }
    except Exception as e:
        logger.error(f"获取机器人状态出�? {e}")
        return {"online": False, "error": str(e)}

# 获取所有插件列�?
def get_plugins():
    """获取插件列表"""
    try:
        plugins = []
        plugins_dir = Path(BASE_DIR) / "plugins"
        
        if not plugins_dir.exists():
            logger.warning(f"插件目录不存�? {plugins_dir}")
            # 创建插件目录
            try:
                os.makedirs(plugins_dir, exist_ok=True)
                logger.info(f"已创建插件目�? {plugins_dir}")
            except Exception as e:
                logger.error(f"创建插件目录失败: {e}")
        
        if plugins_dir.exists() and plugins_dir.is_dir():
            for plugin_dir in plugins_dir.iterdir():
                if plugin_dir.is_dir() and (plugin_dir / "__init__.py").exists():
                    plugin_name = plugin_dir.name
                    plugin = {
                        "name": plugin_name,
                        "enabled": True,  # 默认启用
                        "description": "无描述信�?
                    }
                    
                    # 尝试读取插件�?info.json 文件获取更多信息
                    info_file = plugin_dir / "info.json"
                    if info_file.exists():
                        try:
                            with open(info_file, "r", encoding="utf-8") as f:
                                info = json.load(f)
                                if "name" in info:
                                    plugin["name"] = info["name"]
                                if "description" in info:
                                    plugin["description"] = info["description"]
                                if "version" in info:
                                    plugin["version"] = info["version"]
                                if "author" in info:
                                    plugin["author"] = info["author"]
                                if "enabled" in info:
                                    plugin["enabled"] = info["enabled"]
                        except Exception as e:
                            logger.error(f"读取插件 {plugin_name} 信息出错: {e}")
                    
                    plugins.append(plugin)
        
        return plugins
    except Exception as e:
        logger.error(f"获取插件列表出错: {e}")
        return []

# 获取插件配置
def get_plugin_config(plugin_id: str):
    plugin_config_path = PROJECT_ROOT / "plugins" / plugin_id / "config.toml"
    if not plugin_config_path.exists():
        return None
    
    try:
        with open(plugin_config_path, "rb") as f:
            config_data = tomli.load(f)
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
                return {"success": False, "message": f"插件目录 {plugin_name} 已存�?}
            
            # 克隆Git仓库
            subprocess.run(
                ["git", "clone", "-b", git_branch, git_url, str(plugin_dir)],
                check=True
            )
            
            # 检查配置文�?
            plugin_config = get_plugin_config(plugin_name)
            if not plugin_config:
                # 创建默认配置
                default_config = {
                    "plugin": {
                        "name": plugin_name,
                        "description": "从Git仓库安装的插�?,
                        "version": "1.0.0",
                        "author": "未知"
                    }
                }
                
                with open(plugin_dir / "config.toml", "w") as f:
                    toml.dump(default_config, f)
            
            return {
                "success": True, 
                "message": f"插件 {plugin_name} 已安�?,
                "plugin": {
                    "id": plugin_name,
                    "name": plugin_name,
                    "enabled": True
                }
            }
            
        elif install_type == "local":
            local_path = kwargs.get("local_path")
            
            if not local_path:
                return {"success": False, "message": "未提供本地路�?}
            
            local_path = Path(local_path)
            if not local_path.exists():
                return {"success": False, "message": f"路径 {local_path} 不存�?}
            
            if not local_path.is_dir():
                return {"success": False, "message": f"{local_path} 不是目录"}
            
            # 获取插件名称
            plugin_name = local_path.name
            plugin_dir = plugins_dir / plugin_name
            
            # 检查目标目录是否已存在
            if plugin_dir.exists():
                return {"success": False, "message": f"插件目录 {plugin_name} 已存�?}
            
            # 复制文件
            shutil.copytree(local_path, plugin_dir)
            
            # 检查配置文�?
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
                "message": f"插件 {plugin_name} 已安�?,
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
                return {"success": False, "message": f"插件目录 {plugin_name} 已存�?}
            
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
            
            # 找到主目�?
            extracted_dirs = [d for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))]
            if len(extracted_dirs) == 1:
                # 只有一个目录，使用该目�?
                main_dir = os.path.join(temp_dir, extracted_dirs[0])
            else:
                # 有多个目录，找到包含__init__.py的目�?
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
            
            # 检查配置文�?
            plugin_config = get_plugin_config(plugin_name)
            if not plugin_config:
                # 创建默认配置
                default_config = {
                    "plugin": {
                        "name": plugin_name,
                        "description": "从ZIP文件安装的插�?,
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
                "message": f"插件 {plugin_name} 已安�?,
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
        current_config = tomli.load(f)
    
    disabled_plugins = current_config.get("XYBot", {}).get("disabled-plugins", [])
    
    # 检查插件是否存�?
    plugin_dir = PROJECT_ROOT / "plugins" / plugin_id
    if not plugin_dir.is_dir():
        return {"success": False, "message": f"插件 {plugin_id} 不存�?}
    
    try:
        # 如果在禁用列表中，移�?
        if plugin_id in disabled_plugins:
            disabled_plugins.remove(plugin_id)
            current_config["XYBot"]["disabled-plugins"] = disabled_plugins
            
            with open(config_path, "w", encoding="utf-8") as f:
                toml.dump(current_config, f)
        
        # 如果需要删除文�?
        if delete_files:
            shutil.rmtree(plugin_dir)
        
        return {"success": True, "message": f"插件 {plugin_id} 已删�?}
    except Exception as e:
        logger.error(f"删除插件失败: {e}")
        return {"success": False, "message": f"删除插件失败: {str(e)}"}

# 更新插件
async def update_plugin(plugin_id: str):
    plugin_dir = PROJECT_ROOT / "plugins" / plugin_id
    
    # 检查插件是否存�?
    if not plugin_dir.is_dir():
        return {"success": False, "message": f"插件 {plugin_id} 不存�?}
    
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
        
        # 拉取最新代�?
        subprocess.run(
            ["git", "-C", str(plugin_dir), "pull", "origin", current_branch],
            check=True
        )
        
        return {"success": True, "message": f"插件 {plugin_id} 已更�?}
    except Exception as e:
        logger.error(f"更新插件失败: {e}")
        return {"success": False, "message": f"更新插件失败: {str(e)}"}

# 控制机器�?
def control_robot(action: str):
    if action not in ["start", "stop", "restart"]:
        logger.warning(f"收到不支持的机器人控制操�? {action}")
        return {"success": False, "message": f"不支持的操作: {action}"}
    
    try:
        logger.info(f"执行机器人控制操�? {action}")
        
        if action == "start":
            # 检查是否已经在运行
            running, pid = is_robot_running()
            if running:
                logger.warning("机器人已在运行，无需重复启动")
                return {"success": False, "message": "机器人已在运�?, "status": "running", "pid": pid}
            
            logger.info("正在启动机器�?..")
            
            # 构建启动命令
            cmd = []
            if platform.system() == "Windows":
                cmd = ["python", "main.py"]
            else:
                cmd = ["python3", "main.py"]
            
            # 添加环境变量，确保使用正确的Python和资源路�?
            env = os.environ.copy()
            env["PYTHONPATH"] = str(PROJECT_ROOT)
            
            # 启动机器�?
            try:
                process = subprocess.Popen(
                    cmd, 
                    cwd=str(PROJECT_ROOT),
                    env=env,
                    stdout=subprocess.PIPE if platform.system() == "Windows" else subprocess.DEVNULL,
                    stderr=subprocess.PIPE if platform.system() == "Windows" else subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
                )
                
                logger.info(f"机器人进程启动，PID: {process.pid}")
                
                # 等待启动
                wait_time = 0
                max_wait = 10  # 最多等�?0�?
                check_interval = 0.5  # �?.5秒检查一�?
                
                while wait_time < max_wait:
                    time.sleep(check_interval)
                    wait_time += check_interval
                    
                    # 检查进程是否仍在运�?
                    if process.poll() is not None:
                        # 进程已退�?
                        stdout, stderr = process.communicate()
                        logger.error(f"机器人进程启动失�? 退出码: {process.returncode}")
                        logger.error(f"标准输出: {stdout.decode('utf-8', errors='ignore') if stdout else ''}")
                        logger.error(f"标准错误: {stderr.decode('utf-8', errors='ignore') if stderr else ''}")
                        return {"success": False, "message": f"启动机器人失败，进程异常退出，返回�? {process.returncode}"}
                    
                    # 检查是否已成功启动
                    running, new_pid = is_robot_running()
                    if running:
                        logger.info(f"机器人已成功启动，PID: {new_pid}")
                        
                        # 获取状态并触发通知
                        status = get_robot_status()
                        
                        return {"success": True, "message": "机器人已启动", "pid": new_pid}
                
                # 超过最大等待时�?
                logger.warning("机器人启动超时，但进程仍在运行。请检查日志确认是否正常运行�?)
                return {"success": True, "message": "机器人已启动，但尚未检测到就绪状态，请稍后再检查�?, "pid": process.pid}
                
            except Exception as e:
                logger.error(f"启动机器人时发生异常: {e}")
                return {"success": False, "message": f"启动机器人失�? {str(e)}"}
                
        elif action == "stop":
            # 检查是否在运行
            running, pid = is_robot_running()
            if not running:
                logger.warning("机器人未在运行，无法停止")
                return {"success": False, "message": "机器人未在运�?}
            
            # 先获取当前状态，用于之后的通知
            current_status = get_robot_status()
            
            logger.info(f"正在停止机器人进�?(PID: {pid})...")
            
            try:
                # 获取进程对象
                process = psutil.Process(pid)
                
                # 获取子进�?
                children = process.children(recursive=True)
                
                # 先正常终止主进程
                process.terminate()
                
                # 等待进程终止
                gone, still_alive = psutil.wait_procs([process], timeout=5)
                
                if still_alive:
                    # 如果进程未终止，强制终止
                    logger.warning(f"进程 {pid} 未响应终止信号，正在强制终止...")
                    for p in still_alive:
                        p.kill()
                
                # 终止所有子进程
                if children:
                    logger.info(f"正在终止 {len(children)} 个子进程...")
                    for child in children:
                        try:
                            child.terminate()
                        except psutil.NoSuchProcess:
                            pass
                    
                    # 等待子进程终�?
                    gone, still_alive = psutil.wait_procs(children, timeout=3)
                    
                    # 强制终止仍在运行的子进程
                    if still_alive:
                        for p in still_alive:
                            try:
                                p.kill()
                            except psutil.NoSuchProcess:
                                pass
                
                logger.info("机器人已成功停止")
                
                # 更新状态，但不直接发送通知
                # API端点会在下次请求时检测状态变化并发送通知
                current_status["online"] = False
                
                return {"success": True, "message": "机器人已停止"}
                
            except psutil.NoSuchProcess:
                logger.warning(f"进程 {pid} 不存在，可能已经终止")
                return {"success": True, "message": "机器人已停止（进程不存在�?}
                
            except Exception as e:
                logger.error(f"停止机器人时发生异常: {e}")
                return {"success": False, "message": f"停止机器人失�? {str(e)}"}
            
        elif action == "restart":
            logger.info("正在重启机器�?..")
            
            # 先获取当前状态，用于之后的通知
            current_status = get_robot_status().copy()
            
            # 先停�?
            stop_result = control_robot("stop")
            if not stop_result["success"]:
                logger.warning(f"停止机器人失�? {stop_result['message']}")
                # 如果是因为机器人未运行而停止失败，则继续启�?
                if "未在运行" not in stop_result["message"]:
                    return {"success": False, "message": f"重启失败: {stop_result['message']}"}
            
            # 等待完全停止
            time.sleep(2)
            
            # 启动
            start_result = control_robot("start")
            
            # 返回启动结果
            if start_result["success"]:
                logger.info("机器人已成功重启")
                start_result["message"] = "机器人已重启"
            else:
                logger.error(f"重启机器人失�? {start_result['message']}")
                start_result["message"] = f"重启机器人失�? {start_result['message']}"
            
            return start_result
    
    except Exception as e:
        logger.error(f"控制机器人失�? {e}", exc_info=True)
        return {"success": False, "message": f"控制机器人失�? {str(e)}"}

# 获取二维码URL
def get_qrcode_from_logs():
    """从最新的日志文件中获取登录二维码URL"""
    logger.info("开始从日志中查找二维码URL")
    
    # 尝试多个可能的日志位�?
    possible_log_dirs = [
        Path(PROJECT_ROOT) / "logs",
        Path(PROJECT_ROOT) / "log",
        Path(PROJECT_ROOT),
        Path("/var/log/xbotv2"),
        Path("/logs"),
        Path(".")
    ]
    
    log_files = []
    
    # 检查各个可能的日志目录
    for log_dir in possible_log_dirs:
        if log_dir.exists() and log_dir.is_dir():
            logger.info(f"搜索日志目录: {log_dir}")
            # 获取该目录下所�?log文件
            files = list(log_dir.glob("*.log"))
            if files:
                log_files.extend(files)
                logger.info(f"�?{log_dir} 发现 {len(files)} 个日志文�?)
    
    if not log_files:
        logger.warning("未找到任何日志文�?)
        return None
    
    # 按修改时间排序，最新的优先
    log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    if log_files:
        logger.info(f"共找�?{len(log_files)} 个日志文件，按修改时间排�?)
    else:
        logger.warning("没有找到任何日志文件")
        return None
    
    # 从最新的日志文件开始查找二维码URL
    qr_pattern = re.compile(r'(https?://[^\s]+\.png|https?://[^\s]+weixin[^\s]+)')
    
    for log_file in log_files[:5]:  # 只检查最新的5个文�?
        try:
            logger.info(f"检查日志文�? {log_file}")
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            
            # 倒序查找，最新的日志条目在文件末�?
            for line in reversed(lines):
                if "二维�? in line or "qrcode" in line.lower() or "weixin" in line.lower() or ".png" in line:
                    match = qr_pattern.search(line)
                    if match:
                        qr_url = match.group(0)
                        logger.info(f"在日志中找到二维码URL: {qr_url[:30]}...")
                        return qr_url
        except Exception as e:
            logger.error(f"读取日志文件 {log_file} 时出�? {e}")
            continue
    
    logger.warning("在所有日志文件中未找到二维码URL")
    return None

# 获取最近日志内�?
def get_recent_logs(limit=10, search=None, level=None):
    global _logs_cache
    
    # 确保_logs_cache包含所有必需的字�?
    if not _logs_cache:
        _logs_cache = {
            'last_update': 0,
            'logs': [],
            'cache_timeout': 5  # 默认缓存超时时间�?�?
        }
    elif 'cache_timeout' not in _logs_cache:
        _logs_cache['cache_timeout'] = 5
    
    # 检查缓存是否有�?
    current_time = time.time()
    if (_logs_cache and 
        'last_update' in _logs_cache and
        _logs_cache['last_update'] > current_time - _logs_cache.get("cache_timeout", 5) and
        'logs' in _logs_cache):
        logs = _logs_cache['logs']
        if search or level:
            logs = filter_logs(logs, search, level)
        return logs[:limit]
    
    logs = []
    
    # 可能的日志目�?
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
                logs.append({
                    "time": time.strftime('%Y-%m-%d %H:%M:%S'), 
                    "level": "ERROR", 
                    "content": f"搜索日志文件时出�?{log_dir}/{pattern}: {str(e)}"
                })
    
    if not log_files:
        # 如果没有找到日志文件，返回提示信�?
        sample_logs = []
        
        # 添加示例日志和警�?
        current_time = time.strftime('%Y-%m-%d %H:%M:%S')
        sample_logs.append({
            "time": current_time, 
            "level": "WARNING", 
            "content": "未找到日志文件。请检查以下目录："
        })
        
        for log_dir in log_dirs:
            sample_logs.append({
                "time": current_time, 
                "level": "INFO", 
                "content": f"- {os.path.abspath(log_dir)}"
            })
            
        sample_logs.append({
            "time": current_time, 
            "level": "INFO", 
            "content": "使用日志模式: " + ", ".join(patterns)
        })
        
        sample_logs.append({
            "time": current_time, 
            "level": "WARNING", 
            "content": "请确保XYBot正在运行并生成日志文�?
        })
        
        # 添加示例二维码URL
        qr_time = current_time
        qr_example = f"请使用微信扫描二维码登录: https://open.weixin.qq.com/connect/qrconnect?appid=example"
        sample_logs.append({
            "time": qr_time, 
            "level": "INFO", 
            "content": qr_example
        })
        
        # 更新缓存
        _logs_cache = {
            'last_update': current_time,
            'logs': sample_logs,
            'cache_timeout': 5  # 添加缓存超时
        }
        
        # 返回过滤后的样本日志
        filtered_logs = filter_logs(sample_logs, search, level) if (search or level) else sample_logs
        return filtered_logs[:limit]
    
    # 读取最新的日志文件内容
    logs = []
    
    # 最多读取前5个日志文�?
    for log_file in log_files[:5]:
        try:
            # 获取文件大小
            file_size = os.path.getsize(log_file)
            
            # 如果文件太大，只读取末尾的部�?
            read_size = min(file_size, 50 * 1024)  # 最多读�?0KB
            
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                if read_size < file_size:
                    f.seek(file_size - read_size)
                    # 丢弃第一行，因为可能是不完整�?
                    f.readline()
                
                lines = f.readlines()
                
                # 处理每一行日�?
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 尝试解析日志�?
                    log_entry = parse_log_line(line)
                    if log_entry:
                        logs.append(log_entry)
                    else:
                        # 如果无法解析，作为纯文本添加
                        logs.append({
                            "time": time.strftime('%Y-%m-%d %H:%M:%S'),
                            "level": "INFO",
                            "content": line
                        })
        except Exception as e:
            # 记录读取日志文件时的错误
            logger.error(f"读取日志文件 {log_file} 时出�? {str(e)}")
            logs.append({
                "time": time.strftime('%Y-%m-%d %H:%M:%S'),
                "level": "ERROR",
                "content": f"读取日志文件 {os.path.basename(log_file)} 时出�? {str(e)}"
            })
    
    # 按时间排序，最新的在前
    logs.sort(key=lambda x: x.get('time', ''), reverse=True)
    
    # 记录找到的日志数�?
    logger.info(f"API获取�?{len(logs)} 条日�?)
    
    # 更新缓存
    _logs_cache = {
        'last_update': time.time(),
        'logs': logs,
        'cache_timeout': 5  # 刷新缓存超时
    }
    
    # 返回过滤后的日志
    filtered_logs = filter_logs(logs, search, level) if (search or level) else logs
    return filtered_logs[:limit]

# 解析日志�?
def parse_log_line(line):
    try:
        # 尝试多种日志格式
        # 格式1: [2023-09-10 15:20:45] [INFO] 日志内容
        match1 = re.match(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] \[([A-Z]+)\] (.*)', line)
        if match1:
            return {
                "time": match1.group(1),
                "level": match1.group(2),
                "content": match1.group(3)
            }
        
        # 格式2: 2023-09-10 15:20:45 | INFO | 日志内容
        match2 = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| ([A-Z]+) \| (.*)', line)
        if match2:
            return {
                "time": match2.group(1),
                "level": match2.group(2),
                "content": match2.group(3)
            }
        
        # 格式3: 2023/09/10 15:20:45 [INFO] 日志内容
        match3 = re.match(r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}) \[([A-Z]+)\] (.*)', line)
        if match3:
            return {
                "time": match3.group(1).replace('/', '-'),
                "level": match3.group(2),
                "content": match3.group(3)
            }
        
        # 格式4: [15:20:45] [INFO] 日志内容 (没有日期的情�?
        match4 = re.match(r'\[(\d{2}:\d{2}:\d{2})\] \[([A-Z]+)\] (.*)', line)
        if match4:
            today = time.strftime('%Y-%m-%d')
            return {
                "time": f"{today} {match4.group(1)}",
                "level": match4.group(2),
                "content": match4.group(3)
            }
        
        # 如果无法匹配任何格式，返回None
        return None
    except Exception as e:
        logger.error(f"解析日志行出�? {str(e)} - 行内�? {line}")
        return None

# 路由定义
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, username: str = Depends(get_current_username)):
    """首页/仪表�?""
    try:
        # 获取机器人状�?
        robot_status = get_robot_status()
        
        # 获取系统信息
        system_info = {
            "os": platform.system() + " " + platform.release(),
            "python": platform.python_version(),
            "uptime": get_uptime(),
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent
        }
        
        # 获取最近的日志
        recent_logs = get_recent_logs(5)
        
        # 获取当前配置信息
        config = get_config()
        
        logger.info("渲染首页/仪表板页�?)
        return templates.TemplateResponse("index.html", {
            "request": request,
            "robot": robot_status,
            "system": system_info,
            "logs": recent_logs,
            "config": config,
            "admin_name": username
        })
    except Exception as e:
        logger.error(f"渲染首页出错: {e}")
        logger.error(traceback.format_exc())
        # 返回基本页面信息
        return templates.TemplateResponse("index.html", {
            "request": request,
            "robot": {"status": "未知", "error": str(e)},
            "system": {"error": str(e)},
            "logs": [],
            "config": {},
            "admin_name": username
        })

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, message: str = None):
    """用户登录页面"""
    try:
        # 检查用户是否已经登�?
        if "authenticated" in request.session and request.session.get("authenticated", False):
            # 已登录，重定向到首页
            return RedirectResponse(url="/", status_code=303)
        
        # 未登录，显示登录页面
        return templates.TemplateResponse(
            "user_login.html", 
            {
                "request": request,
                "message": message
            }
        )
    except Exception as e:
        logger.error(f"加载登录页面失败: {e}")
        logger.error(traceback.format_exc())
        return HTMLResponse(f"<h1>加载登录页面失败</h1><p>{str(e)}</p>")

@app.get("/wechat_login", response_class=HTMLResponse)
async def wechat_login_page(request: Request, username: str = Depends(get_current_username)):
    """微信二维码登录页�?""
    try:
        # 获取最新的二维码URL
        qr_link = ""
        try:
            qr_result = get_qrcode_from_logs()
            if qr_result and qr_result.get("success"):
                qr_link = qr_result.get("qrcode_url", "")
        except Exception as qr_error:
            logger.error(f"获取二维码URL失败: {qr_error}")
        
        return templates.TemplateResponse(
            "login.html", 
            {
                "request": request,
                "qr_link": qr_link,
                "admin_name": username
            }
        )
    except Exception as e:
        logger.error(f"渲染微信登录页面出错: {e}")
        logger.error(traceback.format_exc())
        return HTMLResponse(f"<h1>加载微信登录页面失败</h1><p>{str(e)}</p>")

@app.get("/plugins", response_class=HTMLResponse)
async def plugins_page(request: Request, username: str = Depends(get_current_username)):
    """插件管理页面"""
    try:
        # 获取所有插件信�?
        plugins_info = []
        plugins_dir = Path(BASE_DIR) / "plugins"
        
        if not plugins_dir.exists():
            logger.warning(f"插件目录不存�? {plugins_dir}")
            # 创建插件目录
            try:
                os.makedirs(plugins_dir, exist_ok=True)
                logger.info(f"已创建插件目�? {plugins_dir}")
            except Exception as e:
                logger.error(f"创建插件目录失败: {e}")
        
        if plugins_dir.exists() and plugins_dir.is_dir():
            for plugin_dir in plugins_dir.iterdir():
                if plugin_dir.is_dir() and (plugin_dir / "__init__.py").exists():
                    plugin_name = plugin_dir.name
                    plugin_info = {
                        "name": plugin_name,
                        "status": "已安�?,  # 默认状�?
                        "version": "未知",
                        "description": "无描述信�?
                    }
                    
                    # 尝试读取插件�?info.json 文件获取更多信息
                    info_file = plugin_dir / "info.json"
                    if info_file.exists():
                        try:
                            with open(info_file, "r", encoding="utf-8") as f:
                                info_data = json.load(f)
                                plugin_info.update(info_data)
                        except Exception as e:
                            logger.error(f"读取插件 {plugin_name} 的信息出�? {e}")
                    
                    plugins_info.append(plugin_info)
        
        logger.info(f"渲染插件页面，共{len(plugins_info)}个插�?)
        return templates.TemplateResponse("plugins.html", {
            "request": request, 
            "plugins": plugins_info,
            "admin_name": username
        })
    except Exception as e:
        logger.error(f"渲染插件页面出错: {e}")
        logger.error(traceback.format_exc())
        # 返回错误页面或基本插件页�?
        return templates.TemplateResponse("plugins.html", {
            "request": request, 
            "plugins": [],
            "error": str(e),
            "admin_name": username
        })

@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request, username: str = Depends(get_current_username)):
    """日志查看页面"""
    try:
        # 获取最�?0条日�?
        logs = get_recent_logs(20)
        
        # 确保每条日志都包含必要的字段
        formatted_logs = []
        for log in logs:
            # 确保日志有必要的字段
            if isinstance(log, dict) and "message" in log:
                if "timestamp" not in log:
                    log["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if "level" not in log:
                    log["level"] = "INFO"
                formatted_logs.append(log)
        
        logger.info(f"渲染日志页面，共{len(formatted_logs)}条日�?)
        return templates.TemplateResponse("logs.html", {
            "request": request, 
            "logs": formatted_logs,
            "admin_name": username
        })
    except Exception as e:
        logger.error(f"渲染日志页面出错: {e}")
        logger.error(traceback.format_exc())
        # 返回错误页面或基本日志页�?
        return templates.TemplateResponse("logs.html", {
            "request": request, 
            "logs": [
                {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                 "level": "ERROR", 
                 "message": f"加载日志时出�? {str(e)}"}
            ],
            "error": str(e),
            "admin_name": username
        })

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, username: str = Depends(get_current_username)):
    """系统设置页面"""
    try:
        # 使用通用的配置读取函�?
        system_config = get_config()
        if not system_config:
            logger.error("获取配置失败")
            system_config = {}
        
        logger.info("渲染设置页面")
        return templates.TemplateResponse(
            "settings.html", 
            {
                "request": request, 
                "config": system_config,
                "admin_name": username
            }
        )
    except Exception as e:
        logger.error(f"渲染设置页面出错: {e}")
        logger.error(traceback.format_exc())
        return templates.TemplateResponse(
            "settings.html", 
            {
                "request": request, 
                "config": {},
                "error": str(e),
                "admin_name": username
            }
        )

@app.get("/logout")
async def logout(request: Request):
    """处理用户登出请求"""
    try:
        # 清除会话
        request.session.clear()
        logger.info("用户登出成功")
    except Exception as e:
        logger.error(f"登出处理出错: {e}")
        logger.error(traceback.format_exc())
    finally:
        # 无论发生什么错误，都确保重定向到登录页�?
        return RedirectResponse(url="/login", status_code=303)

# 为兼容性保留其他登出路�?
@app.get("/logout2")
@app.get("/logout3")
async def logout_alt(request: Request):
    """兼容性路由，重定向到主登出路�?""
    return await logout(request)

@app.get("/api/status")
async def get_status_api(username: str = Depends(get_current_username)):
    """获取系统状态API接口"""
    try:
        # 获取机器人状�?
        robot_status = get_robot_status()
        
        # 获取系统信息
        system_info = {
            "cpu": psutil.cpu_percent(),
            "memory": psutil.Process().memory_info().rss,
            "memory_percent": psutil.virtual_memory().percent,
            "uptime": int(time.time() - psutil.boot_time())
        }
        
        # 获取Redis连接状�?
        try:
            # 检查是否可以使用socket模块
            has_socket = True
            try:
                import socket
            except ImportError:
                has_socket = False
            
            # 使用socket尝试连接Redis
            redis_running = False
            redis_error = "未检测到Socket�?
            if has_socket:
                # 尝试简单检查Redis连接
                redis_host = config.get("WechatAPIServer", {}).get("redis-host", "127.0.0.1")
                redis_port = config.get("WechatAPIServer", {}).get("redis-port", 6379)
                
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                try:
                    s.connect((redis_host, redis_port))
                    redis_running = True
                    redis_error = None
                except Exception as e:
                    redis_running = False
                    redis_error = f"无法连接到Redis服务�? {redis_host}:{redis_port} - {str(e)}"
                    logger.warning(f"Redis连接失败: {redis_error}")
                finally:
                    s.close()
        except Exception as e:
            redis_running = False
            redis_error = f"检查Redis状态时出错: {str(e)}"
        
        system_info["redis"] = {
            "running": redis_running,
            "error": redis_error
        }
        
        # 获取插件信息
        plugins = get_plugins()
        enabled_plugins = [p for p in plugins if p['enabled']]
        
        plugin_info = {
            "total": len(plugins),
            "enabled": len(enabled_plugins),
            "disabled": len(plugins) - len(enabled_plugins)
        }
        
        # 获取用户信息
        user_info = {
            "wxid": robot_status.get("wxid", ""),
            "nickname": robot_status.get("nickname", ""),
            "alias": robot_status.get("alias", ""),
            "login_time": get_login_time()
        }
        
        # 尝试添加头像URL
        try:
            profile_path = PROJECT_ROOT / "resource" / "profile.json"
            if os.path.exists(profile_path):
                with open(profile_path, "r", encoding="utf-8") as f:
                    profile_data = json.load(f)
                    if "avatar_url" in profile_data:
                        user_info["avatar_url"] = profile_data["avatar_url"]
        except Exception as e:
            logger.warning(f"获取头像URL时出�? {e}")
        
        # 获取消息统计
        message_stats = get_message_stats()
        
        # 检查机器人状态变化，触发通知
        check_robot_status_change(robot_status)
        
        # 返回完整状态信�?
        return {
            "robot": robot_status,
            "system": system_info,
            "plugins": plugin_info,
            "user": user_info,
            "messages": message_stats
        }
    except Exception as e:
        logger.error(f"获取状态信息时出错: {e}")
        logger.error(traceback.format_exc())
        return {
            "robot": {"online": False, "error": str(e)},
            "system": {"error": "获取系统信息失败"},
            "plugins": {"total": 0, "enabled": 0, "disabled": 0},
            "user": {"wxid": "", "nickname": "未登�?, "alias": ""},
            "messages": {"total": 0, "today": 0}
        }

@app.get("/api/plugins")
async def get_plugins_api(username: str = Depends(get_current_username)):
    plugins = get_plugins()
    return {"success": True, "plugins": plugins}

@app.post("/api/plugins/{plugin_id}/toggle")
async def toggle_plugin(plugin_id: str, username: str = Depends(get_current_username)):
    # 读取配置
    current_config = load_toml_config(config_path)
    if not current_config:
        return {"success": False, "message": "读取配置文件失败"}
    
    disabled_plugins = current_config.get("XYBot", {}).get("disabled-plugins", [])
    
    # 检查插件是否存�?
    plugin_dir = PROJECT_ROOT / "plugins" / plugin_id
    if not plugin_dir.is_dir():
        return {"success": False, "message": f"插件 {plugin_id} 不存�?}
    
    # 切换状�?
    if plugin_id in disabled_plugins:
        disabled_plugins.remove(plugin_id)
        new_status = True  # 启用
    else:
        disabled_plugins.append(plugin_id)
        new_status = False  # 禁用
    
    # 更新配置
    current_config["XYBot"]["disabled-plugins"] = disabled_plugins
    
    # 保存配置
    if save_toml_config(config_path, current_config):
        return {"success": True, "message": f"插件 {plugin_id} 已{'启用' if new_status else '禁用'}", "enabled": new_status}
    else:
        return {"success": False, "message": "保存配置文件失败"}

@app.get("/api/plugins/{plugin_id}/config")
async def get_plugin_config_api(plugin_id: str, username: str = Depends(get_current_username)):
    # 获取插件信息
    plugins = get_plugins()
    plugin = next((p for p in plugins if p["id"] == plugin_id), None)
    
    if not plugin:
        return {"success": False, "message": f"插件 {plugin_id} 不存�?}
    
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
    config_data: Dict[str, Any] = FastAPIBody(...),
    username: str = Depends(get_current_username)
):
    plugin_config_path = PROJECT_ROOT / "plugins" / plugin_id / "config.toml"
    
    # 检查插件目�?
    plugin_dir = PROJECT_ROOT / "plugins" / plugin_id
    if not plugin_dir.is_dir():
        return {"success": False, "message": f"插件 {plugin_id} 不存�?}
    
    # 启用/禁用插件
    enabled = config_data.pop("enabled", True)
    main_config = load_toml_config(config_path)
    if not main_config:
        return {"success": False, "message": "读取主配置文件失�?}
    
    disabled_plugins = main_config.get("XYBot", {}).get("disabled-plugins", [])
    
    if not enabled and plugin_id not in disabled_plugins:
        disabled_plugins.append(plugin_id)
    elif enabled and plugin_id in disabled_plugins:
        disabled_plugins.remove(plugin_id)
    
    main_config["XYBot"]["disabled-plugins"] = disabled_plugins
    
    # 保存主配�?
    if not save_toml_config(config_path, main_config):
        return {"success": False, "message": "保存主配置文件失�?}
    
    # 保存插件配置
    if save_toml_config(plugin_config_path, config_data["config"]):
        return {"success": True, "message": "配置已保�?}
    else:
        return {"success": False, "message": "保存插件配置文件失败"}

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
    delete_files: bool = FastAPIBody(False),
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
            
            # 创建WechatAPI客户�?
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
            
            # 获取二维�?
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
            logger.info("开始处理唤醒登录请�?)
            
            # 先尝试控制机器人启动(如果未运�?
            robot_running = is_robot_running()
            logger.info(f"机器人运行状�? {'运行�? if robot_running else '未运�?}")
            
            if not robot_running:
                logger.info("机器人未运行，尝试启�?)
                control_robot("start")
                # 等待机器人启�?
                start_success = False
                for i in range(15):  # 增加等待时间�?5�?
                    logger.info(f"等待机器人启�?..第{i+1}次检�?)
                    if is_robot_running():
                        start_success = True
                        logger.info("机器人已成功启动")
                        break
                    await asyncio.sleep(1)
                
                if not start_success:
                    logger.warning("机器人启动超�?)
            
            # 从日志中获取二维码URL
            logger.info("尝试从日志中获取二维码URL")
            qrcode_url = get_qrcode_from_logs()
            
            if qrcode_url:
                logger.info(f"成功从日志中获取到二维码URL: {qrcode_url[:30]}...")
                # 如果找到二维码URL，使用与扫码登录相同的方式返�?
                login_uuid = str(uuid.uuid4())
                return {
                    "success": True,
                    "method": "qrcode",
                    "url": qrcode_url,
                    "uuid": login_uuid,
                    "device_id": None,
                    "message": "已从日志中找到最新的登录二维�?
                }
            else:
                logger.warning("未从日志中找到二维码URL，尝试唤醒已登录的账�?)
                # 如果没找到二维码URL，使用原来的唤醒登录逻辑
                if not MODULES_LOADED:
                    logger.error("模块未加载，无法继续唤醒登录")
                    return {"success": False, "message": "模块未加载，无法登录"}
                
                try:
                    # 导入WechatAPI
                    import WechatAPI
                    
                    # 创建WechatAPI客户�?
                    api_config = config.get("WechatAPIServer", {})
                    client = WechatAPI.WechatAPIClient("127.0.0.1", api_config.get("port", 9000))
                    
                    # 获取设备信息
                    robot_stat_path = PROJECT_ROOT / "resource" / "robot_stat.json"
                    if os.path.exists(robot_stat_path):
                        logger.info(f"读取机器人状态文�? {robot_stat_path}")
                        try:
                            with open(robot_stat_path, "r") as f:
                                robot_stat = json.load(f)
                            
                            device_name = robot_stat.get("device_name", None)
                            device_id = robot_stat.get("device_id", None)
                            wxid = robot_stat.get("wxid", None)
                            
                            logger.info(f"机器人状态信�? device_name={device_name}, device_id={device_id}, wxid={wxid}")
                        except Exception as e:
                            logger.error(f"读取机器人状态文件失�? {e}")
                            device_name = None
                            device_id = None
                            wxid = None
                    else:
                        logger.warning(f"机器人状态文件不存在: {robot_stat_path}")
                        device_name = None
                        device_id = None
                        wxid = None
                    
                    if not wxid:
                        logger.error("无法找到wxid信息，无法唤醒登�?)
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
                        logger.warning(f"未找到账�?{wxid} 的缓存信�?)
                        login_uuid = str(uuid.uuid4())
                        return {
                            "success": False, 
                            "message": "无法唤醒登录，账号缓存不存在",
                            "uuid": login_uuid,
                            "need_manual": True  # 告诉前端可能需要手动输入URL
                        }
                except Exception as e:
                    logger.error(f"唤醒登录过程中出现异�? {e}")
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
            return {"success": False, "message": "模块未加载，无法检查登录状�?}
        
        # 导入WechatAPI
        import WechatAPI
        
        # 创建WechatAPI客户�?
        api_config = config.get("WechatAPIServer", {})
        client = WechatAPI.WechatAPIClient("127.0.0.1", api_config.get("port", 9000))
        
        # 检查登录状�?
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
        return {"success": False, "message": f"检查登录状态失�? {str(e)}"}

@app.post("/api/settings/save")
async def save_settings(config_data: Dict[str, Any] = FastAPIBody(...), username: str = Depends(get_current_username)):
    try:
        # 读取现有配置
        current_config = load_toml_config(config_path)
        if not current_config:
            return {"success": False, "message": "读取配置文件失败"}
        
        # 更新配置
        for section, settings in config_data.items():
            if isinstance(settings, dict):
                # 处理嵌套配置部分
                if section not in current_config:
                    current_config[section] = {}
                
                for key, value in settings.items():
                    current_config[section][key] = value
            else:
                # 处理顶级配置�?
                current_config[section] = settings
        
        # 保存配置
        if save_toml_config(config_path, current_config):
            return {"success": True, "message": "设置已保�?}
        else:
            return {"success": False, "message": "保存配置文件失败"}
    except Exception as e:
        logger.error(f"保存设置失败: {e}")
        logger.error(traceback.format_exc())
        return {"success": False, "message": f"保存设置失败: {str(e)}"}

@app.get("/api/logs")
async def get_logs_api(limit: int = 10, search: str = None, level: str = None, username: str = Depends(get_current_username)):
    """获取最近的日志接口"""
    try:
        # 确保日志目录存在
        logs_dir = Path(PROJECT_ROOT) / "logs"
        if not logs_dir.exists():
            logs_dir.mkdir(exist_ok=True)
            logger.info(f"创建日志目录: {logs_dir}")
            # 创建一个初始日志文件，以便前端可以看到一些内�?
            with open(logs_dir / "XYBot_init.log", "w", encoding="utf-8") as f:
                f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | INFO | 初始化日志文件\n")
                f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | INFO | 获取到登录二维码: http://weixin.qq.com/x/oudYJBEvV_gnGKNpZ5gF\n")
        
        # 检查日志文件数量，如果超过20个，则保留最新的10�?
        try:
            manage_log_files(logs_dir)
        except Exception as e:
            logger.warning(f"管理日志文件时出�? {e}")
            
        logs = get_recent_logs(limit)
        
        # 根据搜索条件过滤日志
        if search or level:
            logs = filter_logs(logs, search, level)
            
        logger.info(f"API获取�?{len(logs)} 条日�?)
        return {"success": True, "logs": logs}
    except Exception as e:
        logger.error(f"获取日志失败: {e}")
        logger.error(traceback.format_exc())
        return {"success": False, "message": f"获取日志失败: {str(e)}"}

@app.get("/api/logs/download")
async def download_logs_api(username: str = Depends(get_current_username)):
    """下载日志文件"""
    try:
        logs_dir = PROJECT_ROOT / "logs"
        if not logs_dir.exists():
            logs_dir.mkdir(parents=True, exist_ok=True)
            
        # 找出最新的日志文件
        log_files = list(logs_dir.glob("*.log"))
        if not log_files:
            return JSONResponse(content={"success": False, "message": "未找到日志文�?}, status_code=404)
            
        latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
        
        # 返回文件
        return FileResponse(
            path=latest_log, 
            filename=f"XBotV2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            media_type="text/plain"
        )
    except Exception as e:
        logger.error(f"下载日志时出�? {e}")
        return JSONResponse(content={"success": False, "message": f"下载日志失败: {str(e)}"}, status_code=500)

@app.get("/api/events")
async def get_events_api(limit: int = 10, username: str = Depends(get_current_username)):
    """获取系统事件"""
    try:
        # 这里可以从数据库获取系统事件，目前使用日志模�?
        logs = get_recent_logs(limit=limit)
        events = []
        
        # 过滤出重要事�?
        for log in filter_logs(logs, None, None):
            # 检查是否是重要日志
            if "登录" in (log.get("content") or log.get("message") or ""):
                log["event_type"] = "login"
            elif "启动" in (log.get("content") or log.get("message") or ""):
                log["event_type"] = "start"
            elif "错误" in (log.get("content") or log.get("message") or "") or log.get("level") == "ERROR":
                log["event_type"] = "error"
            else:
                log["event_type"] = "info"
                
            events.append(log)
            
        return {"success": True, "events": events}
    except Exception as e:
        logger.error(f"获取系统事件时出�? {e}")
        return {"success": False, "message": f"获取系统事件失败: {str(e)}"}

def filter_logs(logs, search=None, level=None):
    """根据搜索条件过滤日志"""
    if not logs:
        return []
        
    filtered_logs = logs
    
    # 按日志级别过�?
    if level and level.lower() != 'all':
        filtered_logs = [
            log for log in filtered_logs 
            if log and (log.get("level", "").upper() == level.upper() or 
                       (isinstance(log, str) and level.upper() in log.upper()))
        ]
    
    # 按关键词搜索
    if search:
        search_lower = search.lower()
        filtered_logs = []
        for log in logs:
            # 处理对象格式日志
            if isinstance(log, dict):
                content = log.get("content", "") or log.get("message", "")
                if isinstance(content, str) and search_lower in content.lower():
                    filtered_logs.append(log)
            # 处理字符串格式日�?
            elif isinstance(log, str) and search_lower in log.lower():
                filtered_logs.append(log)
    
    # 确保所有日志对象都有content字段
    for log in filtered_logs:
        if isinstance(log, dict) and ("content" not in log or log["content"] is None):
            # 尝试从message字段获取内容
            if "message" in log and log["message"] is not None:
                log["content"] = log["message"]
            else:
                # 设置默认内容
                log["content"] = "(无内�?"
    
    return filtered_logs

def manage_log_files(logs_dir, max_files=20, keep_files=10):
    """管理日志文件数量，防止磁盘空间耗尽"""
    try:
        log_files = list(logs_dir.glob("*.log"))
        if len(log_files) > max_files:
            # 按修改时间排�?
            log_files.sort(key=lambda x: x.stat().st_mtime)
            # 删除较旧的文件，保留最新的keep_files�?
            for old_file in log_files[:-keep_files]:
                try:
                    old_file.unlink()
                    logger.info(f"已删除旧日志文件: {old_file}")
                except Exception as e:
                    logger.warning(f"删除旧日志文件时出错: {e}")
    except Exception as e:
        logger.error(f"管理日志文件时出�? {e}")
        raise

@app.get("/api/plugin_marketplace")
async def get_plugin_marketplace_api(
    category: str = None, 
    query: str = None, 
    limit: int = 50, 
    offset: int = 0, 
    sort_by: str = "updated_at", 
    sort_order: str = "desc",
    username: str = Depends(get_current_username)
):
    """获取插件市场中的插件列表"""
    try:
        # 获取插件仓库实例
        repo = get_plugin_repository()
        
        # 获取插件列表
        plugins, total = repo.get_plugins(
            category=category, 
            query=query, 
            limit=limit, 
            offset=offset, 
            sort_by=sort_by, 
            sort_order=sort_order
        )
        
        return {
            "success": True, 
            "plugins": plugins, 
            "total": total,
            "page": offset // limit + 1,
            "total_pages": (total + limit - 1) // limit
        }
    except Exception as e:
        logger.error(f"获取插件市场数据失败: {e}")
        logger.error(traceback.format_exc())
        return {"success": False, "message": f"获取插件市场数据失败: {str(e)}"}

@app.get("/api/plugin_marketplace/{plugin_id}")
async def get_plugin_details_api(plugin_id: str, username: str = Depends(get_current_username)):
    """获取插件详细信息"""
    try:
        # 获取插件仓库实例
        repo = get_plugin_repository()
        
        # 获取插件详细信息
        plugin = repo.get_plugin_details(plugin_id)
        
        if not plugin:
            return {"success": False, "message": f"插件 {plugin_id} 不存�?}
        
        return {"success": True, "plugin": plugin}
    except Exception as e:
        logger.error(f"获取插件详细信息失败: {e}")
        logger.error(traceback.format_exc())
        return {"success": False, "message": f"获取插件详细信息失败: {str(e)}"}

@app.post("/api/plugin_marketplace/sync")
async def sync_plugin_repositories_api(username: str = Depends(get_current_username)):
    """同步插件仓库数据"""
    try:
        # 获取插件仓库实例
        repo = get_plugin_repository()
        
        # 同步仓库数据
        await repo.sync_repositories()
        
        return {"success": True, "message": "插件仓库同步完成"}
    except Exception as e:
        logger.error(f"同步插件仓库失败: {e}")
        logger.error(traceback.format_exc())
        return {"success": False, "message": f"同步插件仓库失败: {str(e)}"}

@app.post("/api/plugin_marketplace/install/{plugin_id}")
async def install_marketplace_plugin_api(
    plugin_id: str, 
    version: str = None,
    username: str = Depends(get_current_username)
):
    """从插件市场安装插�?""
    try:
        # 获取插件仓库实例
        repo = get_plugin_repository()
        
        # 下载插件
        plugin_file = await repo.download_plugin(plugin_id, version)
        
        # 获取插件信息
        plugin_info = repo.get_plugin_details(plugin_id)
        
        if not plugin_info:
            return {"success": False, "message": f"插件 {plugin_id} 不存�?}
        
        # 调用现有的安装插件函数来完成安装
        result = await install_plugin("zip_file", local_file=plugin_file)
        
        if result.get("success"):
            return {
                "success": True, 
                "message": f"插件 {plugin_info['name']} 安装成功", 
                "plugin_id": result.get("plugin_id")
            }
        else:
            return {"success": False, "message": result.get("message")}
    except Exception as e:
        logger.error(f"安装插件失败: {e}")
        logger.error(traceback.format_exc())
        return {"success": False, "message": f"安装插件失败: {str(e)}"}

@app.get("/api/plugin_marketplace/repositories")
async def get_repositories_api(username: str = Depends(get_current_username)):
    """获取仓库列表"""
    try:
        # 获取插件仓库实例
        repo = get_plugin_repository()
        
        # 获取仓库列表
        repositories = repo.get_repositories()
        
        return {"success": True, "repositories": repositories}
    except Exception as e:
        logger.error(f"获取仓库列表失败: {e}")
        logger.error(traceback.format_exc())
        return {"success": False, "message": f"获取仓库列表失败: {str(e)}"}

@app.post("/api/plugin_marketplace/repositories")
async def add_repository_api(
    url: str = FastAPIBody(...),
    name: str = FastAPIBody(...),
    description: str = FastAPIBody(""),
    username: str = Depends(get_current_username)
):
    """添加插件仓库"""
    try:
        # 获取插件仓库实例
        repo = get_plugin_repository()
        
        # 添加仓库
        repo.add_repository(url, name, description)
        
        return {"success": True, "message": f"仓库 {name} 添加成功"}
    except Exception as e:
        logger.error(f"添加仓库失败: {e}")
        logger.error(traceback.format_exc())
        return {"success": False, "message": f"添加仓库失败: {str(e)}"}

@app.delete("/api/plugin_marketplace/repositories/{url:path}")
async def remove_repository_api(url: str, username: str = Depends(get_current_username)):
    """删除插件仓库"""
    try:
        # 获取插件仓库实例
        repo = get_plugin_repository()
        
        # 删除仓库
        repo.remove_repository(url)
        
        return {"success": True, "message": f"仓库删除成功"}
    except Exception as e:
        logger.error(f"删除仓库失败: {e}")
        logger.error(traceback.format_exc())
        return {"success": False, "message": f"删除仓库失败: {str(e)}"}

@app.put("/api/plugin_marketplace/repositories/{url:path}")
async def update_repository_status_api(
    url: str, 
    enabled: bool = FastAPIBody(...),
    username: str = Depends(get_current_username)
):
    """更新仓库状�?""
    try:
        # 获取插件仓库实例
        repo = get_plugin_repository()
        
        # 更新仓库状�?
        repo.update_repository_status(url, enabled)
        
        return {"success": True, "message": f"仓库状态更新成�?}
    except Exception as e:
        logger.error(f"更新仓库状态失�? {e}")
        logger.error(traceback.format_exc())
        return {"success": False, "message": f"更新仓库状态失�? {str(e)}"}

@app.post("/api/plugin_marketplace/rating/{plugin_id}")
async def add_plugin_rating_api(
    plugin_id: str,
    rating: int = FastAPIBody(...),
    comment: str = FastAPIBody(""),
    username: str = Depends(get_current_username)
):
    """为插件添加评分和评论"""
    try:
        # 获取插件仓库实例
        repo = get_plugin_repository()
        
        # 添加评分
        repo.add_plugin_rating(plugin_id, username, rating, comment)
        
        return {"success": True, "message": "评分提交成功"}
    except Exception as e:
        logger.error(f"添加评分失败: {e}")
        logger.error(traceback.format_exc())
        return {"success": False, "message": f"添加评分失败: {str(e)}"}

# 在应用启动时初始化插件仓�?
@app.on_event("startup")
async def startup_plugin_repository():
    """启动时初始化插件仓库"""
    # 确保所有必要目录存�?
    ensure_directories()
    
    try:
        from database.plugin_repository import init_plugin_repository
        logger.info("初始化插件仓�?..")
        init_plugin_repository()
        logger.info("插件仓库初始化完�?)
    except Exception as e:
        logger.error(f"初始化插件仓库失�? {e}")
        logger.error(traceback.format_exc())

# 主函�?
def start_web_server():
    """启动Web服务�?""
    try:
        # 确保目录存在
        ensure_directories()
        
        # 获取配置
        config = get_config()
        web_config = config.get("WebInterface", {})
        
        host = web_config.get("host", "0.0.0.0")
        port = web_config.get("port", 8080)
        debug = web_config.get("debug", False)
        
        # 确保port是整�?
        try:
            port = int(port)
        except (ValueError, TypeError):
            logger.warning(f"端口配置格式不正�? {port}，使用默认�?080")
            port = 8080
        
        logger.info(f"启动Web服务�? {host}:{port}，调试模�? {'开�? if debug else '关闭'}")
        
        # 记录系统信息
        import platform
        import psutil
        logger.info(f"操作系统: {platform.system()} {platform.release()} {platform.machine()}")
        logger.info(f"Python版本: {platform.python_version()}")
        logger.info(f"系统内存: {psutil.virtual_memory().total / (1024*1024*1024):.2f} GB")
        logger.info(f"CPU信息: {platform.processor()} ({psutil.cpu_count()} 核心)")
        
        try:
            # 记录主要依赖版本
            import fastapi
            import uvicorn
            import jinja2
            import sqlalchemy
            import loguru
            logger.info(f"依赖版本 - FastAPI: {fastapi.__version__}, Uvicorn: {uvicorn.__version__}, Jinja2: {jinja2.__version__}, SQLAlchemy: {sqlalchemy.__version__}")
        except Exception as dep_error:
            logger.warning(f"获取依赖版本信息失败: {dep_error}")
        
        # 启动服务�?
        try:
            uvicorn.run("web.app:app", host=host, port=port, reload=debug)
        except Exception as run_error:
            logger.error(f"uvicorn.run失败: {run_error}")
            logger.error(traceback.format_exc())
            
            # 尝试备选启动方�?
            import uvicorn.config
            import asyncio
            config = uvicorn.config.Config(app=app, host=host, port=port)
            server = uvicorn.Server(config)
            logger.info("使用备选方法启动服务器")
            asyncio.run(server.serve())
            
    except Exception as e:
        logger.error(f"启动Web服务器失�? {e}")
        logger.error(traceback.format_exc())
        raise

# 在其他页面路由附近添加以下代�?
@app.get("/plugin_marketplace", response_class=HTMLResponse)
async def get_plugin_marketplace_page(request: Request, username: str = Depends(get_current_username)):
    """插件市场页面"""
    # 获取插件分类
    categories = ["工具", "娱乐", "信息", "社交", "数据", "科学", "办公", "其他"]
    
    return templates.TemplateResponse(
        "plugin_marketplace.html", 
        {
            "request": request,
            "categories": categories,
            "admin_name": username
        }
    )

@app.get("/api/settings")
async def get_settings_api(username: str = Depends(get_current_username)):
    """获取系统设置API接口"""
    try:
        # 读取现有配置
        config = get_config()
        if not config:
            return {"success": False, "message": "读取配置文件失败"}
        
        return {"success": True, "data": config}
    except Exception as e:
        logger.error(f"获取设置失败: {e}")
        logger.error(traceback.format_exc())
        return {"success": False, "message": f"获取设置失败: {str(e)}"}

@app.get("/api/messages")
async def get_messages_api(
    page: int = 1, 
    limit: int = 10, 
    search: str = None, 
    username: str = Depends(get_current_username)
):
    """获取消息列表API接口"""
    try:
        # 获取消息数据
        # 临时模拟数据，用于前端测�?
        mock_messages = [
            {
                "id": "1",
                "sender": "张三 (wxid_123456)",
                "content": "你好，这是一条测试消�?,
                "type": "text",
                "timestamp": int(time.time() - 3600 * 5) * 1000  # 5小时�?
            },
            {
                "id": "2",
                "sender": "李四 (wxid_234567)",
                "content": "https://example.com/image.jpg",
                "type": "image",
                "timestamp": int(time.time() - 3600 * 3) * 1000  # 3小时�?
            },
            {
                "id": "3",
                "sender": "测试�?(23456789@chatroom)",
                "content": "这是来自群聊的消�?,
                "type": "text",
                "timestamp": int(time.time() - 3600 * 1) * 1000  # 1小时�?
            },
            {
                "id": "4",
                "sender": "系统通知",
                "content": "机器人已成功登录",
                "type": "system",
                "timestamp": int(time.time() - 600) * 1000  # 10分钟�?
            },
            {
                "id": "5",
                "sender": "王五 (wxid_345678)",
                "content": "https://example.com/voice.mp3",
                "type": "voice",
                "timestamp": int(time.time() - 300) * 1000  # 5分钟�?
            }
        ]
        
        # 如果有搜索参数，过滤消息
        if search:
            search = search.lower()
            mock_messages = [
                msg for msg in mock_messages 
                if search in msg["sender"].lower() or search in msg["content"].lower()
            ]
        
        # 分页信息
        total_messages = len(mock_messages)
        total_pages = max(1, math.ceil(total_messages / limit))
        current_page = min(page, total_pages)
        
        # 计算当前页的消息
        start_idx = (current_page - 1) * limit
        end_idx = start_idx + limit
        page_messages = mock_messages[start_idx:end_idx]
        
        return {
            "messages": page_messages,
            "total": total_messages,
            "page": page,
            "limit": limit,
            "pages": total_pages
        }
    except Exception as e:
        logger.error(f"获取消息失败: {e}")
        logger.error(traceback.format_exc())
    return await logout(request)

if __name__ == "__main__":
    start_web_server() 

