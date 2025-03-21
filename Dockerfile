FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 添加编译所需的依赖
RUN apt-get update && apt-get install -y gcc python3-dev

# 首先复制requirements.txt
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir requests

# 过滤掉问题依赖并安装其他依赖
RUN grep -v -E "matplotlib~=3.10.0|pysilk>=0.5" requirements.txt > requirements_filtered.txt && \
    echo "matplotlib~=3.9.0" >> requirements_filtered.txt && \
    pip install --no-cache-dir -r requirements_filtered.txt

# 复制项目文件
COPY . /app/

# 确保目录结构存在
RUN if [ ! -f "/app/web_ui/middlewares/error_handlers.py" ]; then \
    mkdir -p /app/web_ui/middlewares /app/web_ui/utils && \
    echo '"""中间件包"""\n\nfrom .error_handlers import *' > /app/web_ui/middlewares/__init__.py && \
    echo '"""错误处理中间件"""\n\nimport logging\nfrom fastapi import Request\nfrom fastapi.responses import JSONResponse\n\nlogger = logging.getLogger(__name__)\n\nasync def catch_exceptions_middleware(request: Request, call_next):\n    """全局异常捕获中间件"""\n    try:\n        return await call_next(request)\n    except Exception as e:\n        logger.exception(f"未捕获的异常: {str(e)}")\n        return JSONResponse(status_code=500, content={"detail": "服务器内部错误"})\n' > /app/web_ui/middlewares/error_handlers.py && \
    touch /app/web_ui/utils/__init__.py; \
fi

# 尝试安装xywechatpad-binary
RUN echo "尝试安装xywechatpad-binary..." && \
    mkdir -p wheels && \
    python3 scripts/download_wheel.py || \
    if [ -d "xywechatpad-binary" ]; then \
      echo "尝试从本地安装xywechatpad-binary" && \
      pip install -e xywechatpad-binary; \
    elif [ -d "wheels" ] && [ -f "$(find wheels -name 'xywechatpad-binary*.whl' 2>/dev/null)" ]; then \
      echo "尝试从wheel安装xywechatpad-binary" && \
      pip install $(find wheels -name 'xywechatpad-binary*.whl'); \
    else \
      echo "警告: 无法安装 xywechatpad-binary 包，微信API功能将不可用"; \
    fi

# 设置环境变量
ENV PYTHONPATH=/app

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["uvicorn", "web_ui.app:app", "--host", "0.0.0.0", "--port", "8080"]

