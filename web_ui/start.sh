#!/bin/bash

# 设置工作目录
cd /app || exit 1

# 运行资源修复脚本
echo "运行资源修复脚本..."
bash web_ui/fix_resources.sh

# 检查并修复目录权限
echo "修复目录权限..."
find web_ui -type d -exec chmod 755 {} \; 2>/dev/null || true
find web_ui -type f -exec chmod 644 {} \; 2>/dev/null || true
chmod -R 755 web_ui/static 2>/dev/null || true

# 启动应用
echo "启动应用..."
exec uvicorn web_ui.app:app --host 0.0.0.0 --port 8000 