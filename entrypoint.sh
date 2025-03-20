#!/bin/bash
set -e

# 运行资源修复脚本
if [ -f "/app/web_ui/fix_resources.sh" ]; then
    echo "检查前端资源..."
    bash /app/web_ui/fix_resources.sh
fi

# 修复权限
echo "修复目录权限..."
find /app/web_ui -type d -exec chmod 755 {} \; 2>/dev/null || true
find /app/web_ui -type f -exec chmod 644 {} \; 2>/dev/null || true

# 执行原始命令
exec "$@"