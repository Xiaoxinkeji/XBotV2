from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from .middlewares import catch_exceptions_middleware, validation_exception_handler, http_exception_handler
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html
)
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import logging
import sys
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from datetime import datetime
import psutil
import subprocess

# 导入新增的中间件和工具
from .middlewares.wechat_monitor import WechatMonitorMiddleware
from .utils.wechat_utils import init_wechat_connection, check_wechat_connection
from .utils.service_recovery import start_wechat_service

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('web_ui.log')
    ]
)

logger = logging.getLogger("web_ui")

# 创建应用
app = FastAPI(
    title="XYBot Web管理界面",
    description="XYBot微信机器人的Web可视化管理系统",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
)

# 设置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加微信监控中间件
app.add_middleware(WechatMonitorMiddleware)

# 静态文件
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent / "static"),
    name="static"
)

# 模板
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# 导入路由
from web_ui.routers import plugins, users, stats, messages, status, dashboard, auth, health, wechat
app.include_router(plugins.router, prefix="/api/plugins", tags=["plugins"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
app.include_router(messages.router, prefix="/api/messages", tags=["messages"])
app.include_router(status.router, prefix="/api/status", tags=["status"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(wechat.router, prefix="/api/wechat", tags=["wechat"])

# 注册中间件
app.middleware("http")(catch_exceptions_middleware)

# 注册异常处理器
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)

# 安全相关中间件
app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "*"]
)

# 启用Gzip压缩
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 首页路由
@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "XYBot管理面板"}
    )

# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "OK", "version": "1.0.0"}

# API文档配置
@app.get("/api/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - API文档",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.1.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.1.0/swagger-ui.css",
    )

@app.get("/api/docs/oauth2-redirect", include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "title": "XYBot - 登录"}
    )

@app.on_event("startup")
async def startup_event():
    """应用启动时执行初始化任务"""
    # 检查资源文件
    resource_script = os.path.join(os.path.dirname(__file__), "fix_resources.sh")
    if os.path.exists(resource_script):
        try:
            logger.info("正在检查前端资源文件...")
            subprocess.run(["bash", resource_script], check=True)
            logger.info("前端资源检查完成")
        except subprocess.SubprocessError as e:
            logger.error(f"资源修复脚本执行失败: {str(e)}")
    
    # 初始化微信连接
    try:
        logger.info("正在初始化微信API连接...")
        is_connected = await check_wechat_connection()
        
        if is_connected:
            logger.info("微信API连接成功")
        else:
            logger.warning("微信API连接失败，尝试启动服务...")
            service_started = await start_wechat_service()
            
            if service_started:
                logger.info("微信API服务启动成功")
                # 再次检查连接
                is_connected = await check_wechat_connection()
                if is_connected:
                    logger.info("微信API现在已连接")
                else:
                    logger.warning("微信API服务已启动但连接仍失败，请检查配置")
            else:
                logger.error("微信API服务启动失败，请手动检查")
    except Exception as e:
        logger.error(f"初始化微信API连接失败: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("Web管理界面关闭中")

@app.on_event("startup")
async def startup_db_client():
    from database.session import init_db
    try:
        await init_db()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        logger.warning("部分功能可能无法正常工作")

# 将导入移到函数内部以避免循环导入
def get_sessions():
    from web_ui.routers.auth import SESSIONS
    return SESSIONS

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            # 使用函数获取会话存储
            SESSIONS = get_sessions()
            
            # 不需要验证的路径
            exempt_paths = ["/login", "/api/auth/login", "/api/auth/check", "/health", "/static"]
            
            # 检查路径是否需要验证
            is_exempt = False
            for path in exempt_paths:
                if request.url.path.startswith(path):
                    is_exempt = True
                    break
            
            if is_exempt:
                return await call_next(request)
            
            # 检查是否有有效的会话
            session_id = request.cookies.get("session_id")
            
            # API请求直接返回401错误
            if request.url.path.startswith("/api/"):
                if not session_id or session_id not in SESSIONS:
                    return JSONResponse(
                        status_code=401,
                        content={"success": False, "message": "未登录或会话已过期"}
                    )
                
                # 检查会话是否过期
                session = SESSIONS.get(session_id)
                if datetime.now() > session.get("expires", datetime.now()):
                    SESSIONS.pop(session_id, None)
                    return JSONResponse(
                        status_code=401,
                        content={"success": False, "message": "会话已过期"}
                    )
            
            # 页面请求重定向到登录页
            elif not session_id or session_id not in SESSIONS:
                return RedirectResponse(url="/login")
            
            # 通过验证，继续处理请求
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"认证中间件错误: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": "服务器内部错误"}
            )

# 添加认证中间件
app.add_middleware(AuthMiddleware)

@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc):
    return templates.TemplateResponse(
        "404.html",
        {"request": request},
        status_code=404
    )

@app.exception_handler(500)
async def server_error_exception_handler(request: Request, exc):
    return templates.TemplateResponse(
        "500.html",
        {"request": request, "error": str(exc)},
        status_code=500
    )

@app.get("/diagnostic")
async def diagnostic_page(request: Request):
    return templates.TemplateResponse(
        "diagnostic.html",
        {"request": request}
    )

@app.get("/test")
async def test_page(request: Request):
    return templates.TemplateResponse(
        "test.html",
        {"request": request}
    )

@app.get("/minimal")
async def minimal_page(request: Request):
    return templates.TemplateResponse(
        "minimal.html",
        {"request": request}
    )

@app.get("/simple")
async def simple_page(request: Request):
    return templates.TemplateResponse(
        "simple.html",
        {"request": request}
    )

@app.get("/wechat-login")
async def wechat_login_page(request: Request):
    return templates.TemplateResponse(
        "wechat_login.html",
        {"request": request}
    )

@app.get("/offline")
async def offline_page(request: Request):
    return templates.TemplateResponse(
        "offline.html",
        {"request": request}
    ) 