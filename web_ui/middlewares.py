from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import traceback
from typing import Union
from pydantic import ValidationError

logger = logging.getLogger("web_ui")

async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logger.error(f"未捕获的异常: {str(e)}")
        logger.error(traceback.format_exc())
        
        # 返回JSON错误响应
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "服务器内部错误",
                "detail": str(e) if not isinstance(e, ValidationError) else "数据验证错误"
            }
        )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证错误"""
    logger.warning(f"参数验证错误: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "message": "请求参数错误",
            "detail": str(exc)
        }
    )

async def http_exception_handler(request: Request, exc: Union[StarletteHTTPException, HTTPException]):
    """处理HTTP异常"""
    logger.warning(f"HTTP异常: {exc.status_code} - {str(exc.detail)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": str(exc.detail),
        }
    ) 