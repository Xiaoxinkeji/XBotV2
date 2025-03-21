#!/bin/bash
# 启动Redis服务
redis-server /etc/redis/redis.conf &

# 确保日志目录存在
mkdir -p logs

# 启动机器人
python main.py