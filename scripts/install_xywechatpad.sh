#!/bin/bash

# 设置颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}尝试安装 xywechatpad-binary 包...${NC}"

# 定义可能的安装位置
POSSIBLE_DIRS=(
    "xywechatpad-binary"
    "wheels"
    "WechatAPIDocs"
    "vendor/xywechatpad-binary"
    "dependencies/xywechatpad-binary"
)

# 检查并尝试从源码目录安装
for dir in "${POSSIBLE_DIRS[@]}"; do
    if [ -d "$dir" ] && [ "$dir" = "xywechatpad-binary" -o -d "$dir/xywechatpad-binary" ]; then
        PACKAGE_DIR="$dir"
        if [ "$dir" != "xywechatpad-binary" ]; then
            PACKAGE_DIR="$dir/xywechatpad-binary"
        fi
        
        echo -e "${GREEN}找到源码目录: $PACKAGE_DIR, 尝试安装...${NC}"
        if pip install -e "$PACKAGE_DIR"; then
            echo -e "${GREEN}成功从源码安装 xywechatpad-binary${NC}"
            exit 0
        fi
    fi
done

# 检查并尝试从wheel文件安装
for dir in "${POSSIBLE_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        WHEEL_FILE=$(find "$dir" -name "xywechatpad-binary*.whl" 2>/dev/null | head -1)
        if [ -n "$WHEEL_FILE" ]; then
            echo -e "${GREEN}找到wheel文件: $WHEEL_FILE, 尝试安装...${NC}"
            if pip install "$WHEEL_FILE"; then
                echo -e "${GREEN}成功从wheel安装 xywechatpad-binary${NC}"
                exit 0
            fi
        fi
    fi
done

# 检查并尝试从requirements.txt安装
for dir in "${POSSIBLE_DIRS[@]}"; do
    REQ_FILE="$dir/requirements.txt"
    if [ -f "$REQ_FILE" ] && grep -q "xywechatpad-binary" "$REQ_FILE"; then
        echo -e "${GREEN}在 $REQ_FILE 中找到依赖信息, 尝试安装...${NC}"
        if pip install -r "$REQ_FILE"; then
            echo -e "${GREEN}成功从requirements安装 xywechatpad-binary${NC}"
            exit 0
        fi
    fi
done

# 尝试直接从PyPI安装
echo -e "${YELLOW}尝试从PyPI安装 xywechatpad-binary==1.1.0...${NC}"
if pip install xywechatpad-binary==1.1.0; then
    echo -e "${GREEN}成功从PyPI安装 xywechatpad-binary${NC}"
    exit 0
fi

# 所有尝试都失败
echo -e "${RED}无法安装 xywechatpad-binary，微信API功能将不可用${NC}"
exit 1 