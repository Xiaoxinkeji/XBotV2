#!/usr/bin/env python3
"""
检查并修复缺失的文件
"""
import os
import sys
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("fix_files")

def ensure_dir(directory):
    """确保目录存在"""
    Path(directory).mkdir(parents=True, exist_ok=True)
    return directory

def write_file(path, content):
    """写入文件内容"""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"已创建文件: {path}")
        return True
    except Exception as e:
        logger.error(f"写入文件 {path} 时出错: {str(e)}")
        return False

def fix_middleware_files():
    """修复中间件文件"""
    middlewares_dir = ensure_dir("web_ui/middlewares")
    
    # 创建 __init__.py
    init_content = '''"""
中间件包
"""

from .error_handlers import (
    catch_exceptions_middleware,
    validation_exception_handler,
    http_exception_handler,
    setup_error_handlers
)

__all__ = [
    'catch_exceptions_middleware',
    'validation_exception_handler',
    'http_exception_handler',
    'setup_error_handlers'
]
'''
    write_file(os.path.join(middlewares_dir, "__init__.py"), init_content)
    
    # 创建 error_handlers.py
    error_handlers_content = '''"""
错误处理中间件
"""

import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

logger = logging.getLogger(__name__)

async def catch_exceptions_middleware(request: Request, call_next):
    """全局异常捕获中间件"""
    try:
        return await call_next(request)
    except Exception as e:
        logger.exception(f"未捕获的异常: {str(e)}")
        # 记录请求信息以便调试
        logger.error(f"请求路径: {request.url.path}")
        logger.error(f"请求方法: {request.method}")
        logger.error(f"客户端: {request.client}")
        
        # 返回友好的错误响应
        return JSONResponse(
            status_code=500,
            content={"detail": "服务器内部错误，请稍后再试或联系管理员"},
        )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证错误处理器"""
    error_detail = exc.errors()
    logger.warning(f"请求验证失败: {error_detail}")
    
    # 简化错误消息
    simplified_errors = []
    for error in error_detail:
        simplified_errors.append({
            "loc": error.get("loc", []),
            "msg": error.get("msg", "验证错误"),
            "type": error.get("type", "")
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "请求数据验证失败",
            "errors": simplified_errors
        },
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    logger.warning(f"HTTP异常: {exc.status_code} {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )

def setup_error_handlers(app: FastAPI):
    """设置错误处理程序"""
    app.middleware("http")(catch_exceptions_middleware)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
'''
    write_file(os.path.join(middlewares_dir, "error_handlers.py"), error_handlers_content)

def main():
    """主函数"""
    logger.info("开始检查并修复缺失的文件...")
    
    # 确保工具目录存在
    ensure_dir("web_ui/utils")
    write_file("web_ui/utils/__init__.py", '"""工具函数包"""')
    
    # 修复中间件文件
    fix_middleware_files()
    
    logger.info("文件修复完成!")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 