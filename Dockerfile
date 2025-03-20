FROM python:3.9

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV TZ=Asia/Shanghai
ENV IMAGEIO_FFMPEG_EXE=/usr/bin/ffmpeg
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_NO_CACHE_DIR=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    redis-server \
    gcc \
    python3-dev \
    libpq-dev \
    build-essential \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 复制 Redis 配置
COPY redis.conf /etc/redis/redis.conf

# 先安装基础依赖
RUN pip install --upgrade pip wheel setuptools

# 复制依赖文件
COPY requirements.txt .

# 添加编译 psutil 所需的依赖
RUN apt-get update && apt-get install -y gcc python3-dev

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . /app/

# 准备资源脚本
COPY web_ui/fix_resources.sh /app/web_ui/fix_resources.sh
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /app/web_ui/fix_resources.sh /entrypoint.sh

# 设置入口点
ENTRYPOINT ["/entrypoint.sh"]

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "web_ui.app:app", "--host", "0.0.0.0", "--port", "8000"]

