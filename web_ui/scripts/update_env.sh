#!/bin/bash

# 创建环境变量配置文件
if [ ! -f .env ]; then
    echo "创建环境变量配置文件..."
    cat > .env << EOF
# 微信API配置
WECHAT_API_HOST=localhost
WECHAT_API_PORT=5000
WECHAT_API_TOKEN=

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# 服务恢复配置
WECHAT_SERVICE_NAME=wechat-service
MAX_RECOVERY_ATTEMPTS=3
EOF
    echo ".env 文件已创建"
fi

# 加载环境变量
if [ -f .env ]; then
    echo "加载环境变量..."
    export $(grep -v '^#' .env | xargs)
    echo "环境变量已加载"
fi 