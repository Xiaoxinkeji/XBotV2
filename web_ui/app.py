from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path

# 创建应用
app = FastAPI(
    title="XYBot Web管理界面",
    description="XYBot微信机器人的Web可视化管理系统",
    version="1.0.0"
)

# 设置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent / "static"),
    name="static"
)

# 模板
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# 导入路由
from web_ui.routers import plugins, users, stats, messages
app.include_router(plugins.router, prefix="/api/plugins", tags=["插件管理"])
app.include_router(users.router, prefix="/api/users", tags=["用户管理"])
app.include_router(stats.router, prefix="/api/stats", tags=["数据统计"])
app.include_router(messages.router, prefix="/api/messages", tags=["消息管理"])

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