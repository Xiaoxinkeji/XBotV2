#!/bin/bash
set -e

echo "启动 XBotV2 服务..."

# 确保Redis服务正在运行
echo "启动Redis服务: redis-server"
service redis-server start || {
    echo "Redis服务启动失败，但会继续执行"
}

# 确保python环境正确
echo "Python版本检查:"
python --version

# 确保目录结构
echo "设置目录结构..."
mkdir -p /app/logs
mkdir -p /app/resource
mkdir -p /app/database
mkdir -p /app/web/templates
mkdir -p /app/web/static
mkdir -p /app/plugins
mkdir -p /var/log/xbotv2

# 设置目录权限
echo "设置目录权限..."
chmod -R 755 /var/log/xbotv2
chmod -R 755 /app/logs
chmod -R 755 /app/resource
chmod -R 755 /app/database
chmod -R 755 /app/web
chmod -R 755 /app/plugins

# 检查关键依赖是否已安装
echo "检查关键依赖..."
python -c "
import importlib.util, subprocess, os, sys
import traceback

# 关键依赖列表
required_modules = [
    'fastapi', 'uvicorn', 'starlette', 'itsdangerous', 
    'tomli', 'toml', 'tomllib', 'jinja2', 'aiohttp', 'requests', 
    'loguru', 'sqlalchemy', 'pydantic', 'python-multipart'
]

# 检查并安装缺失的模块
missing_modules = []
for module in required_modules:
    try:
        importlib.util.find_spec(module)
        print(f'模块 {module} 已安装')
    except ImportError:
        print(f'错误: 模块 {module} 未安装')
        missing_modules.append(module)
    except Exception as e:
        print(f'检查模块 {module} 时出错: {e}')

# 特别处理tomli/tomllib (Python 3.11+的标准库)
try:
    import tomllib
    print('使用Python 3.11+ 内置的tomllib')
except ImportError:
    try:
        import tomli
        print('使用tomli库')
    except ImportError:
        try:
            import toml
            print('使用toml库')
        except ImportError:
            print('错误: 未找到任何TOML解析库！添加tomli到安装列表')
            if 'tomli' not in missing_modules:
                missing_modules.append('tomli')

# 批量安装缺失的模块
if missing_modules:
    print(f'安装缺失模块: {missing_modules}')
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_modules)
        print('缺失模块已安装')
    except Exception as e:
        print(f'安装模块失败: {e}')
        print(traceback.format_exc())
        # 单独安装每个模块
        for module in missing_modules:
            try:
                print(f'尝试单独安装 {module}...')
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', module])
                print(f'模块 {module} 已成功安装')
            except Exception as e:
                print(f'安装 {module} 失败: {e}')
"

# 如果是首次运行，创建样例日志文件
if [ ! -f "/app/logs/xbotv2.log" ]; then
    echo "创建示例日志文件..."
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] XBotV2服务启动" > /app/logs/xbotv2.log
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] 日志系统初始化成功" >> /app/logs/xbotv2.log
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] 等待登录微信..." >> /app/logs/xbotv2.log
fi

# 确保配置文件存在
if [ ! -f "/app/main_config.toml" ]; then
    echo "警告: 未找到配置文件，创建默认配置..."
    cat > /app/main_config.toml << EOF
[WechatAPIServer]
port = 9000
mode = "release"
redis-host = "localhost"
redis-port = 6379
redis-password = ""
redis-db = 0

[XYBot]
version = "v1.0.0"
ignore-protection = false
XYBotDB-url = "sqlite:///database/xybot.db"
msgDB-url = "sqlite+aiosqlite:///database/message.db"
keyvalDB-url = "sqlite+aiosqlite:///database/keyval.db"
admins = [ "admin-wxid", ]
disabled-plugins = [ ]
timezone = "Asia/Shanghai"
auto-restart = false

[WebInterface]
enable = true
port = 8080
host = "0.0.0.0"
debug = false
username = "admin"
password = "admin123"

[Notification]
enable = true
pushplus-token = ""
notify-online = true
notify-offline = true
online-title = "机器人已上线"
offline-title = "机器人已掉线"
ignore-mode = "None"
whitelist = [ ]
blacklist = [ ]
EOF
    echo "已创建默认配置文件"
fi

# 设置Python环境变量
export PYTHONUNBUFFERED=1
export PYTHONIOENCODING=utf-8
export PYTHONPATH=/app:$PYTHONPATH

# 检查是否可以导入关键模块
cd /app
python -c "
try:
    from utils.config_utils import load_toml_config
    print('成功导入config_utils模块')
    from pathlib import Path
    config = load_toml_config(Path('/app/main_config.toml'))
    print(f'成功读取配置文件，包含以下部分: {list(config.keys()) if config else []}')
except Exception as e:
    import traceback
    print(f'导入或读取配置时出错: {e}')
    print(traceback.format_exc())
"

# 启动XBotV2主程序
echo "启动XBotV2主程序..."
export XBOT_SKIP_VERSION_CHECK=1
python main.py