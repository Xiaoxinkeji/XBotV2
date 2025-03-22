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
mkdir -p /app/web/templates
mkdir -p /app/web/static
mkdir -p /app/plugins

# 设置目录权限
chmod -R 755 /var/log/xbotv2
chmod -R 755 /app/logs
chmod -R 755 /app/resource
chmod -R 755 /app/database
chmod -R 755 /app/web
chmod -R 755 /app/plugins

# 检查关键依赖是否已安装
echo "Checking for required dependencies..."
python -c "
import importlib.util, subprocess

# 关键依赖列表
required_modules = [
    'fastapi', 'uvicorn', 'starlette', 'itsdangerous', 
    'tomli', 'toml', 'jinja2', 'aiohttp', 'requests', 
    'loguru', 'sqlalchemy', 'pydantic'
]

# 检查并安装缺失的模块
missing_modules = []
for module in required_modules:
    if importlib.util.find_spec(module) is None:
        print(f'ERROR: Required module {module} is not installed')
        missing_modules.append(module)
    else:
        print(f'Module {module} is installed')

# 批量安装缺失的模块
if missing_modules:
    print(f'Installing missing modules: {missing_modules}')
    subprocess.check_call(['pip', 'install'] + missing_modules)
    print('Missing modules have been installed')
"

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
# 允许跳过Python版本检查
export XBOT_SKIP_VERSION_CHECK=1
python main.py