from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.middleware.sessions import SessionMiddleware

import json
import logging
import platform
import psutil
import os
import sys
import time
import traceback
import secrets
# 处理tomli与toml的兼容性
try:
    import tomli  # Python 3.11前的TOML解析
except ImportError:
    tomli = None
    
import toml  # 通用TOML解析库
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

# 配置日志
logger = logging.getLogger("web")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/web.log", encoding="utf-8")
    ]
)

# 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logger.info(f"项目根目录: {BASE_DIR}")

# 获取系统运行时间的辅助函数
def get_uptime():
    """获取系统运行时间"""
    try:
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        days, seconds = uptime.days, uptime.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{days}天 {hours}小时 {minutes}分钟"
    except Exception as e:
        logger.error(f"获取系统运行时间出错: {e}")
        return "未知"

app = FastAPI(title="XBotV2 Web管理",
              description="XBotV2微信机器人的Web管理界面",
              version="1.0")

# 添加会话中间件
app.add_middleware(
    SessionMiddleware, 
    secret_key=secrets.token_urlsafe(32),  # 使用随机生成的密钥
    session_cookie="xbotv2_session",
    max_age=3600  # 会话有效期1小时
)

# 配置模板和静态文件
templates_path = Path(BASE_DIR) / "web" / "templates"
if not templates_path.exists():
    templates_path = Path(BASE_DIR) / "templates"
    if not templates_path.exists():
        logger.error(f"找不到模板目录: {templates_path}")
        os.makedirs(templates_path, exist_ok=True)
logger.info(f"使用模板目录: {templates_path}")
templates = Jinja2Templates(directory=str(templates_path))

static_path = Path(BASE_DIR) / "web" / "static"
if not static_path.exists():
    static_path = Path(BASE_DIR) / "static"
    if not static_path.exists():
        logger.error(f"找不到静态文件目录: {static_path}")
        os.makedirs(static_path, exist_ok=True)
logger.info(f"使用静态文件目录: {static_path}")
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# 配置相关函数
def get_config():
    """获取当前配置"""
    try:
        config_path = Path(BASE_DIR) / "main_config.toml"
        with open(config_path, "rb") as f:
            # 优先使用tomli，如果不可用则使用toml
            if tomli:
                return tomli.load(f)
            else:
                # toml库需要文本而非二进制模式
                f.close()
                with open(config_path, "r", encoding="utf-8") as f2:
                    return toml.load(f2)
    except Exception as e:
        logger.error(f"读取配置文件出错: {e}")
        logger.error(traceback.format_exc())
        return {}

# 用户认证相关函数
security = HTTPBasic()

def get_current_username(request: Request):
    """从会话中获取当前用户名，如未认证则重定向到登录页"""
    authenticated = request.session.get("authenticated", False)
    if not authenticated:
        logger.warning("用户未认证，重定向到登录页")
        raise HTTPException(
            status_code=303,
            detail="Not authenticated",
            headers={"Location": "/login"}
        )
    return request.session.get("username", "anonymous")

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
    """获取机器人状态"""
    try:
        # 这里应该是实际检查机器人状态的代码
        # 为简化，这里返回一个示例状态
        return {
            "online": True,
            "wxid": "wxid_example",
            "nickname": "XBot机器人",
            "alias": "XBot",
            "plugin_count": 5,
            "message_count": 100
        }
    except Exception as e:
        logger.error(f"获取机器人状态出错: {e}")
        return {"online": False, "error": str(e)}

# 获取所有插件列表
def get_plugins():
    """获取插件列表"""
    try:
        plugins = []
        plugins_dir = Path(BASE_DIR) / "plugins"
        
        if plugins_dir.exists() and plugins_dir.is_dir():
            for plugin_dir in plugins_dir.iterdir():
                if plugin_dir.is_dir() and (plugin_dir / "__init__.py").exists():
                    plugin_name = plugin_dir.name
                    plugin = {
                        "name": plugin_name,
                        "enabled": True,  # 默认启用
                        "description": "无描述信息"
                    }
                    
                    # 尝试读取插件的 info.json 文件获取更多信息
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
        current_config = tomli.load(f)
    
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
            
            with open(config_path, "w", encoding="utf-8") as f:
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
        logger.warning(f"收到不支持的机器人控制操作: {action}")
        return {"success": False, "message": f"不支持的操作: {action}"}
    
    try:
        logger.info(f"执行机器人控制操作: {action}")
        
        if action == "start":
            # 检查是否已经在运行
            running, pid = is_robot_running()
            if running:
                logger.warning("机器人已在运行，无需重复启动")
                return {"success": False, "message": "机器人已在运行", "status": "running", "pid": pid}
            
            logger.info("正在启动机器人...")
            
            # 构建启动命令
            cmd = []
            if platform.system() == "Windows":
                cmd = ["python", "main.py"]
            else:
                cmd = ["python3", "main.py"]
            
            # 添加环境变量，确保使用正确的Python和资源路径
            env = os.environ.copy()
            env["PYTHONPATH"] = str(PROJECT_ROOT)
            
            # 启动机器人
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
                max_wait = 10  # 最多等待10秒
                check_interval = 0.5  # 每0.5秒检查一次
                
                while wait_time < max_wait:
                    time.sleep(check_interval)
                    wait_time += check_interval
                    
                    # 检查进程是否仍在运行
                    if process.poll() is not None:
                        # 进程已退出
                        stdout, stderr = process.communicate()
                        logger.error(f"机器人进程启动失败, 退出码: {process.returncode}")
                        logger.error(f"标准输出: {stdout.decode('utf-8', errors='ignore') if stdout else ''}")
                        logger.error(f"标准错误: {stderr.decode('utf-8', errors='ignore') if stderr else ''}")
                        return {"success": False, "message": f"启动机器人失败，进程异常退出，返回码: {process.returncode}"}
                    
                    # 检查是否已成功启动
                    running, new_pid = is_robot_running()
                    if running:
                        logger.info(f"机器人已成功启动，PID: {new_pid}")
                        
                        # 获取状态并触发通知
                        status = get_robot_status()
                        
                        return {"success": True, "message": "机器人已启动", "pid": new_pid}
                
                # 超过最大等待时间
                logger.warning("机器人启动超时，但进程仍在运行。请检查日志确认是否正常运行。")
                return {"success": True, "message": "机器人已启动，但尚未检测到就绪状态，请稍后再检查。", "pid": process.pid}
                
            except Exception as e:
                logger.error(f"启动机器人时发生异常: {e}")
                return {"success": False, "message": f"启动机器人失败: {str(e)}"}
                
        elif action == "stop":
            # 检查是否在运行
            running, pid = is_robot_running()
            if not running:
                logger.warning("机器人未在运行，无法停止")
                return {"success": False, "message": "机器人未在运行"}
            
            # 先获取当前状态，用于之后的通知
            current_status = get_robot_status()
            
            logger.info(f"正在停止机器人进程 (PID: {pid})...")
            
            try:
                # 获取进程对象
                process = psutil.Process(pid)
                
                # 获取子进程
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
                    
                    # 等待子进程终止
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
                return {"success": True, "message": "机器人已停止（进程不存在）"}
                
            except Exception as e:
                logger.error(f"停止机器人时发生异常: {e}")
                return {"success": False, "message": f"停止机器人失败: {str(e)}"}
            
        elif action == "restart":
            logger.info("正在重启机器人...")
            
            # 先获取当前状态，用于之后的通知
            current_status = get_robot_status().copy()
            
            # 先停止
            stop_result = control_robot("stop")
            if not stop_result["success"]:
                logger.warning(f"停止机器人失败: {stop_result['message']}")
                # 如果是因为机器人未运行而停止失败，则继续启动
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
                logger.error(f"重启机器人失败: {start_result['message']}")
                start_result["message"] = f"重启机器人失败: {start_result['message']}"
            
            return start_result
    
    except Exception as e:
        logger.error(f"控制机器人失败: {e}", exc_info=True)
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
    
    # 确保_logs_cache包含所有必需的字段
    if not _logs_cache:
        _logs_cache = {
            'last_update': 0,
            'logs': [],
            'cache_timeout': 5  # 默认缓存超时时间为5秒
        }
    elif 'cache_timeout' not in _logs_cache:
        _logs_cache['cache_timeout'] = 5
    
    # 检查缓存是否有效
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
                logs.append({
                    "time": time.strftime('%Y-%m-%d %H:%M:%S'), 
                    "level": "ERROR", 
                    "content": f"搜索日志文件时出错 {log_dir}/{pattern}: {str(e)}"
                })
    
    if not log_files:
        # 如果没有找到日志文件，返回提示信息
        sample_logs = []
        
        # 添加示例日志和警告
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
            "content": "请确保XYBot正在运行并生成日志文件"
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
    
    # 最多读取前5个日志文件
    for log_file in log_files[:5]:
        try:
            # 获取文件大小
            file_size = os.path.getsize(log_file)
            
            # 如果文件太大，只读取末尾的部分
            read_size = min(file_size, 50 * 1024)  # 最多读取50KB
            
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                if read_size < file_size:
                    f.seek(file_size - read_size)
                    # 丢弃第一行，因为可能是不完整的
                    f.readline()
                
                lines = f.readlines()
                
                # 处理每一行日志
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 尝试解析日志行
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
            logger.error(f"读取日志文件 {log_file} 时出错: {str(e)}")
            logs.append({
                "time": time.strftime('%Y-%m-%d %H:%M:%S'),
                "level": "ERROR",
                "content": f"读取日志文件 {os.path.basename(log_file)} 时出错: {str(e)}"
            })
    
    # 按时间排序，最新的在前
    logs.sort(key=lambda x: x.get('time', ''), reverse=True)
    
    # 记录找到的日志数量
    logger.info(f"API获取到 {len(logs)} 条日志")
    
    # 更新缓存
    _logs_cache = {
        'last_update': time.time(),
        'logs': logs,
        'cache_timeout': 5  # 刷新缓存超时
    }
    
    # 返回过滤后的日志
    filtered_logs = filter_logs(logs, search, level) if (search or level) else logs
    return filtered_logs[:limit]

# 解析日志行
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
        
        # 格式4: [15:20:45] [INFO] 日志内容 (没有日期的情况)
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
        logger.error(f"解析日志行出错: {str(e)} - 行内容: {line}")
        return None

# 路由定义
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, username: str = Depends(get_current_username)):
    """首页/仪表板"""
    try:
        # 获取机器人状态
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
        
        logger.info("渲染首页/仪表板页面")
        return templates.TemplateResponse("index.html", {
            "request": request,
            "robot": robot_status,
            "system": system_info,
            "logs": recent_logs,
            "config": config
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
            "config": {}
        })

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, message: str = None):
    """登录页面"""
    try:
        logger.info("渲染登录页面")
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "message": message}
        )
    except Exception as e:
        logger.error(f"渲染登录页面出错: {e}")
        logger.error(traceback.format_exc())
        # 返回基本的HTML登录表单，确保用户至少能够登录
        return HTMLResponse(content="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>登录 - XBotV2</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <link rel="stylesheet" href="/static/css/bootstrap.min.css">
            </head>
            <body class="bg-light">
                <div class="container mt-5">
                    <div class="row justify-content-center">
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header">登录</div>
                                <div class="card-body">
                                    <form action="/auth" method="post">
                                        <div class="mb-3">
                                            <label for="username" class="form-label">用户名</label>
                                            <input type="text" class="form-control" id="username" name="username" required>
                                        </div>
                                        <div class="mb-3">
                                            <label for="password" class="form-label">密码</label>
                                            <input type="password" class="form-control" id="password" name="password" required>
                                        </div>
                                        <button type="submit" class="btn btn-primary">登录</button>
                                    </form>
                                    <p class="text-danger mt-3">错误: """ + str(e) + """</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </body>
            </html>
        """)

@app.get("/plugins", response_class=HTMLResponse)
async def plugins_page(request: Request, username: str = Depends(get_current_username)):
    """插件管理页面"""
    try:
        # 获取所有插件信息
        plugins_info = []
        plugins_dir = Path(BASE_DIR) / "plugins"
        
        if plugins_dir.exists() and plugins_dir.is_dir():
            for plugin_dir in plugins_dir.iterdir():
                if plugin_dir.is_dir() and (plugin_dir / "__init__.py").exists():
                    plugin_name = plugin_dir.name
                    plugin_info = {
                        "name": plugin_name,
                        "status": "已安装",  # 默认状态
                        "version": "未知",
                        "description": "无描述信息"
                    }
                    
                    # 尝试读取插件的 info.json 文件获取更多信息
                    info_file = plugin_dir / "info.json"
                    if info_file.exists():
                        try:
                            with open(info_file, "r", encoding="utf-8") as f:
                                info_data = json.load(f)
                                plugin_info.update(info_data)
                        except Exception as e:
                            logger.error(f"读取插件 {plugin_name} 的信息出错: {e}")
                    
                    plugins_info.append(plugin_info)
        
        logger.info(f"渲染插件页面，共{len(plugins_info)}个插件")
        return templates.TemplateResponse("plugins.html", {
            "request": request, 
            "plugins": plugins_info
        })
    except Exception as e:
        logger.error(f"渲染插件页面出错: {e}")
        logger.error(traceback.format_exc())
        # 返回错误页面或基本插件页面
        return templates.TemplateResponse("plugins.html", {
            "request": request, 
            "plugins": [],
            "error": str(e)
        })

@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request, username: str = Depends(get_current_username)):
    """日志查看页面"""
    try:
        # 获取最近20条日志
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
        
        logger.info(f"渲染日志页面，共{len(formatted_logs)}条日志")
        return templates.TemplateResponse("logs.html", {
            "request": request, 
            "logs": formatted_logs
        })
    except Exception as e:
        logger.error(f"渲染日志页面出错: {e}")
        logger.error(traceback.format_exc())
        # 返回错误页面或基本日志页面
        return templates.TemplateResponse("logs.html", {
            "request": request, 
            "logs": [
                {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                 "level": "ERROR", 
                 "message": f"加载日志时出错: {str(e)}"}
            ],
            "error": str(e)
        })

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, username: str = Depends(get_current_username)):
    """系统设置页面"""
    with open(config_path, "rb") as f:
        system_config = tomli.load(f)
    return templates.TemplateResponse("settings.html", {"request": request, "config": system_config})

@app.get("/logout")
async def logout(request: Request):
    """注销登录"""
    response = RedirectResponse(url="/")
    response.delete_cookie(key="session")
    return response

@app.get("/api/status")
async def get_status_api(username: str = Depends(get_current_username)):
    """获取系统状态API接口"""
    try:
        # 获取机器人状态
        robot_status = get_robot_status()
        
        # 获取系统信息
        system_info = {
            "cpu": psutil.cpu_percent(),
            "memory": psutil.Process().memory_info().rss,
            "memory_percent": psutil.virtual_memory().percent,
            "uptime": int(time.time() - psutil.boot_time())
        }
        
        # 获取Redis连接状态
        try:
            # 检查是否已加载需要的模块
            MODULES_LOADED = True
            try:
                import socket
            except ImportError:
                MODULES_LOADED = False
            
            # 使用socket尝试连接Redis
            redis_running = False
            redis_error = "未检测到Redis库"
            if MODULES_LOADED:
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
                    redis_error = f"Redis连接失败: {str(e)}"
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
            logger.warning(f"获取头像URL时出错: {e}")
        
        # 获取消息统计
        message_stats = get_message_stats()
        
        # 检查机器人状态变化，触发通知
        check_robot_status_change(robot_status)
        
        # 返回完整状态信息
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
            "user": {"wxid": "", "nickname": "未登录", "alias": ""},
            "messages": {"total": 0, "today": 0}
        }

@app.get("/api/plugins")
async def get_plugins_api(username: str = Depends(get_current_username)):
    plugins = get_plugins()
    return {"success": True, "plugins": plugins}

@app.post("/api/plugins/{plugin_id}/toggle")
async def toggle_plugin(plugin_id: str, username: str = Depends(get_current_username)):
    # 读取配置
    with open(config_path, "rb") as f:
        current_config = tomli.load(f)
    
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
        # 保存配置 - 使用toml库而不是tomllib
        with open(config_path, "w", encoding="utf-8") as f:
            toml.dump(current_config, f)
        
        return {"success": True, "message": f"插件 {plugin_id} 已{'启用' if new_status else '禁用'}", "enabled": new_status}
    except Exception as e:
        logger.error(f"保存配置失败: {e}")
        logger.error(traceback.format_exc())
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
        main_config = tomli.load(f)
    
    disabled_plugins = main_config.get("XYBot", {}).get("disabled-plugins", [])
    
    if not enabled and plugin_id not in disabled_plugins:
        disabled_plugins.append(plugin_id)
    elif enabled and plugin_id in disabled_plugins:
        disabled_plugins.remove(plugin_id)
    
    main_config["XYBot"]["disabled-plugins"] = disabled_plugins
    
    try:
        # 保存主配置 - 使用toml库而不是tomllib
        with open(config_path, "w", encoding="utf-8") as f:
            toml.dump(main_config, f)
        
        # 保存插件配置
        with open(plugin_config_path, "w", encoding="utf-8") as f:
            toml.dump(config_data["config"], f)
        
        return {"success": True, "message": "配置已保存"}
    except Exception as e:
        logger.error(f"保存插件配置失败: {e}")
        logger.error(traceback.format_exc())
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
        # 读取现有配置
        with open(config_path, "rb") as f:
            current_config = tomli.load(f)
        
        # 更新配置
        for section, settings in config_data.items():
            if isinstance(settings, dict):
                # 处理嵌套配置部分
                if section not in current_config:
                    current_config[section] = {}
                
                for key, value in settings.items():
                    current_config[section][key] = value
            else:
                # 处理顶级配置项
                current_config[section] = settings
        
        # 保存配置 - 使用toml库而不是tomllib
        with open(config_path, "w", encoding="utf-8") as f:
            toml.dump(current_config, f)
        
        return {"success": True, "message": "设置已保存"}
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
            return JSONResponse(content={"success": False, "message": "未找到日志文件"}, status_code=404)
            
        latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
        
        # 返回文件
        return FileResponse(
            path=latest_log, 
            filename=f"XBotV2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            media_type="text/plain"
        )
    except Exception as e:
        logger.error(f"下载日志时出错: {e}")
        return JSONResponse(content={"success": False, "message": f"下载日志失败: {str(e)}"}, status_code=500)

@app.get("/api/events")
async def get_events_api(limit: int = 10, username: str = Depends(get_current_username)):
    """获取系统事件"""
    try:
        # 这里可以从数据库获取系统事件，目前使用日志模拟
        logs = get_recent_logs(limit=limit)
        events = []
        
        # 过滤出重要事件
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
        logger.error(f"获取系统事件时出错: {e}")
        return {"success": False, "message": f"获取系统事件失败: {str(e)}"}

def filter_logs(logs, search=None, level=None):
    """根据搜索条件过滤日志"""
    if not logs:
        return []
        
    filtered_logs = logs
    
    # 按日志级别过滤
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
            # 处理字符串格式日志
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
                log["content"] = "(无内容)"
    
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
            return {"success": False, "message": f"插件 {plugin_id} 不存在"}
        
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
    """从插件市场安装插件"""
    try:
        # 获取插件仓库实例
        repo = get_plugin_repository()
        
        # 下载插件
        plugin_file = await repo.download_plugin(plugin_id, version)
        
        # 获取插件信息
        plugin_info = repo.get_plugin_details(plugin_id)
        
        if not plugin_info:
            return {"success": False, "message": f"插件 {plugin_id} 不存在"}
        
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
    url: str = Body(...),
    name: str = Body(...),
    description: str = Body(""),
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
    enabled: bool = Body(...),
    username: str = Depends(get_current_username)
):
    """更新仓库状态"""
    try:
        # 获取插件仓库实例
        repo = get_plugin_repository()
        
        # 更新仓库状态
        repo.update_repository_status(url, enabled)
        
        return {"success": True, "message": f"仓库状态更新成功"}
    except Exception as e:
        logger.error(f"更新仓库状态失败: {e}")
        logger.error(traceback.format_exc())
        return {"success": False, "message": f"更新仓库状态失败: {str(e)}"}

@app.post("/api/plugin_marketplace/rating/{plugin_id}")
async def add_plugin_rating_api(
    plugin_id: str,
    rating: int = Body(...),
    comment: str = Body(""),
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

# 在应用启动时初始化插件仓库
@app.on_event("startup")
async def startup_plugin_repository():
    """在应用启动时初始化插件仓库"""
    try:
        # 初始化插件仓库
        init_plugin_repository()
        logger.info("插件仓库初始化完成")
    except Exception as e:
        logger.error(f"初始化插件仓库失败: {e}")
        logger.error(traceback.format_exc())

# 主函数
def start_web_server():
    host = web_config.get("host", "0.0.0.0")
    port = web_config.get("port", 8080)
    debug = web_config.get("debug", False)
    
    uvicorn.run("web.app:app", host=host, port=port, reload=debug)

# 在其他页面路由附近添加以下代码
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
        with open(config_path, "rb") as f:
            system_config = tomli.load(f)
        
        return {"success": True, "data": system_config}
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
        # 这里实际应该从数据库读取消息记录
        # 当前为了解决模板缺失错误，我们返回模拟数据
        
        # 模拟的消息数据
        mock_messages = [
            {
                "id": "1",
                "sender": "张三 (wxid_123456)",
                "content": "你好，这是一条测试消息",
                "type": "text",
                "timestamp": int(time.time() - 3600 * 5) * 1000  # 5小时前
            },
            {
                "id": "2",
                "sender": "李四 (wxid_234567)",
                "content": "https://example.com/image.jpg",
                "type": "image",
                "timestamp": int(time.time() - 3600 * 3) * 1000  # 3小时前
            },
            {
                "id": "3",
                "sender": "测试群 (23456789@chatroom)",
                "content": "这是来自群聊的消息",
                "type": "text",
                "timestamp": int(time.time() - 3600 * 1) * 1000  # 1小时前
            },
            {
                "id": "4",
                "sender": "系统通知",
                "content": "机器人已成功登录",
                "type": "system",
                "timestamp": int(time.time() - 600) * 1000  # 10分钟前
            },
            {
                "id": "5",
                "sender": "王五 (wxid_345678)",
                "content": "https://example.com/voice.mp3",
                "type": "voice",
                "timestamp": int(time.time() - 300) * 1000  # 5分钟前
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
        
        # 返回数据
        return {
            "success": True,
            "messages": page_messages,
            "pagination": {
                "current_page": current_page,
                "total_pages": total_pages,
                "total_records": total_messages,
                "limit": limit
            }
        }
    except Exception as e:
        logger.error(f"获取消息列表失败: {e}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "message": f"获取消息列表失败: {str(e)}"
        }

@app.post("/auth")
async def authenticate(request: Request, username: str = Form(...), password: str = Form(...)):
    """处理用户登录请求"""
    try:
        # 从配置文件获取用户名和密码进行验证
        config = get_config()
        admin_username = config.get("Admin", {}).get("username", "admin")
        admin_password = config.get("Admin", {}).get("password", "admin")
        
        logger.info(f"用户登录尝试: {username}")
        
        if username == admin_username and password == admin_password:
            # 登录成功，设置会话
            request.session["authenticated"] = True
            request.session["username"] = username
            logger.info(f"用户 {username} 登录成功")
            # 重定向到首页
            return RedirectResponse(url="/", status_code=303)
        else:
            # 登录失败
            logger.warning(f"用户 {username} 登录失败: 用户名或密码错误")
            return templates.TemplateResponse(
                "login.html", 
                {"request": request, "message": "用户名或密码错误"}
            )
    except Exception as e:
        logger.error(f"登录处理出错: {e}")
        logger.error(traceback.format_exc())
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "message": f"登录处理出错: {str(e)}"}
        )

@app.get("/logout")
async def logout(request: Request):
    """处理用户登出请求"""
    try:
        # 清除会话
        request.session.clear()
        logger.info("用户登出成功")
        return RedirectResponse(url="/login", status_code=303)
    except Exception as e:
        logger.error(f"登出处理出错: {e}")
        return RedirectResponse(url="/login", status_code=303)

# 获取日志
def get_recent_logs(limit=20):
    """获取最近的日志记录"""
    try:
        logs = []
        log_file = Path(BASE_DIR) / "logs" / "web.log"
        
        if log_file.exists():
            with open(log_file, "r", encoding="utf-8") as f:
                # 读取最后N行
                lines = f.readlines()
                last_lines = lines[-limit:] if len(lines) > limit else lines
                
                for line in last_lines:
                    # 解析日志格式：时间 - 模块 - 级别 - 消息
                    parts = line.strip().split(" - ", 3)
                    if len(parts) >= 4:
                        timestamp, module, level, message = parts
                        logs.append({
                            "timestamp": timestamp,
                            "module": module,
                            "level": level,
                            "message": message
                        })
        
        return logs
    except Exception as e:
        logger.error(f"获取日志记录出错: {e}")
        return [{"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                "level": "ERROR", 
                "message": f"无法读取日志: {str(e)}"}]

if __name__ == "__main__":
    start_web_server() 