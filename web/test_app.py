from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import re
import traceback
from pathlib import Path
from datetime import datetime
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("web-app")

# 设置项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

app = FastAPI()

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头部
)

# 获取最近日志内容
def get_recent_logs(limit=10):
    """获取最近的日志内容"""
    logger.info(f"获取最近 {limit} 条日志")
    
    # 样例日志数据
    return [
        {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "level": "INFO", "content": "测试日志内容"},
        {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "level": "WARNING", "content": "这是一条警告信息"},
        {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "level": "ERROR", "content": "这是一条错误信息"},
        {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "level": "INFO", "content": "获取到登录二维码: http://weixin.qq.com/x/oudYJBEvV_gnGKNpZ5gF"}
    ]

@app.get("/")
async def root():
    return {"message": "Hello XBot API"}

@app.get("/api/logs")
async def get_logs_api(limit: int = 10):
    """获取最近的日志接口"""
    try:
        logs = get_recent_logs(limit)
        logger.info(f"API获取到 {len(logs)} 条日志")
        return {"success": True, "logs": logs}
    except Exception as e:
        logger.error(f"获取日志失败: {e}")
        logger.error(traceback.format_exc())
        return {"success": False, "message": f"获取日志失败: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080) 