#!/bin/bash
set -e

echo "Starting XBotV2 services..."

# 确保Redis服务正在运行
echo "Starting redis-server: redis-server."
service redis-server start

# 创建必要的目录
echo "Setting up directories..."
mkdir -p /var/log/xbotv2
mkdir -p /app/logs
mkdir -p /app/resource
mkdir -p /app/database

# 设置日志目录权限
chmod -R 755 /var/log/xbotv2
chmod -R 755 /app/logs

# 如果是首次运行，创建样例日志文件
if [ ! -f "/app/logs/xbotv2.log" ]; then
    echo "Creating sample log file..."
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] XBotV2服务启动" > /app/logs/xbotv2.log
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] 日志系统初始化成功" >> /app/logs/xbotv2.log
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] 等待登录微信..." >> /app/logs/xbotv2.log
fi

# 设置Python环境变量
export PYTHONUNBUFFERED=1

# 启动XBotV2主程序（包含机器人核心和Web服务）
cd /app
python main.py