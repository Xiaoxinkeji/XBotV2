from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import logging
import sys
import os
import traceback

router = APIRouter()
logger = logging.getLogger("web_ui.debug")

@router.get("/api/debug/info")
async def debug_info():
    """提供系统诊断信息，帮助排除问题"""
    try:
        # 收集系统信息
        info = {
            "python_version": sys.version,
            "environment": dict(os.environ),
            "modules": list(sys.modules.keys()),
            "paths": sys.path,
            "platform": sys.platform
        }
        
        # 尝试导入关键模块
        import_status = {}
        for module in ["fastapi", "aiohttp", "WechatAPI", "redis"]:
            try:
                __import__(module)
                import_status[module] = "成功"
            except ImportError as e:
                import_status[module] = f"失败: {str(e)}"
        
        info["imports"] = import_status
        
        return JSONResponse({
            "code": 200,
            "message": "调试信息获取成功",
            "data": info
        })
    except Exception as e:
        logger.error(f"获取调试信息出错: {str(e)}")
        tb = traceback.format_exc()
        return JSONResponse({
            "code": 500,
            "message": f"获取调试信息失败: {str(e)}",
            "error": str(e),
            "traceback": tb,
            "type": str(type(e))
        }, status_code=500)

@router.get("/debug")
async def debug_page(request: Request):
    """调试页面，显示关键系统信息"""
    from ..main import templates
    return templates.TemplateResponse(
        "debug.html",
        {"request": request}
    ) 