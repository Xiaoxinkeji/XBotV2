FROM python:3.11-slim

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
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 复制 Redis 配置
COPY redis.conf /etc/redis/redis.conf

# 先安装基础依赖
RUN pip install --upgrade pip wheel setuptools

# 复制依赖文件
COPY requirements.txt .

# 分步安装依赖，先安装数据库相关依赖
RUN pip install SQLAlchemy==2.0.37 aiosqlite==0.18.0

# 安装图像和媒体相关依赖
RUN pip install pillow==10.4.0 qrcode==8.0 moviepy==2.1.2 pysilk-mod==1.6.4 pymediainfo==7.0.1

# 安装Web相关依赖
RUN pip install fastapi==0.110.0 uvicorn==0.27.1 jinja2==3.1.3 python-multipart==0.0.9 aiofiles==23.2.1

# 安装其他必要依赖
RUN pip install tomli==2.0.1 tomli_w==1.0.0 redis==5.0.1 python-dotenv==1.0.0

# 使用wheel安装psutil
RUN pip install --only-binary=:all: psutil==5.9.6

# 安装剩余依赖
RUN pip install -r requirements.txt || echo "部分依赖安装失败，继续构建"

# 复制应用代码
COPY . .

# 启动脚本
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# 暴露端口
EXPOSE 8080

CMD ["./entrypoint.sh"]

