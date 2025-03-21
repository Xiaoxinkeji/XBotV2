FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    redis-server \
    procps \
    gcc \
    g++ \
    python3-dev \
    make \
    libffi-dev \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements.txt
COPY requirements.txt .

# 先安装必要的基础包
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制其余项目文件
COPY . .

# 创建日志目录并设置权限
RUN mkdir -p /var/log/xbotv2 \
    && mkdir -p /app/logs \
    && mkdir -p /app/resource \
    && mkdir -p /app/database \
    && chmod -R 755 /var/log/xbotv2 \
    && chmod -R 755 /app/logs

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 使entrypoint脚本可执行
RUN chmod +x entrypoint.sh

# 暴露服务端口
EXPOSE 8080

# 设置入口点
ENTRYPOINT ["/app/entrypoint.sh"]

