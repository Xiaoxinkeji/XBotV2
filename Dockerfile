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
COPY . .

# 确保目录结构存在
RUN mkdir -p /app/web_ui/middlewares /app/web_ui/utils && \
    touch /app/web_ui/middlewares/__init__.py /app/web_ui/utils/__init__.py

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

