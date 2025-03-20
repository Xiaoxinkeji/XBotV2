#!/bin/bash

# 设置颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}开始安装依赖...${NC}"

# 安装不包含问题包的依赖
echo -e "${YELLOW}安装基础依赖...${NC}"
grep -v "xywechatpad-binary" requirements.txt > requirements_filtered.txt
pip install -r requirements_filtered.txt

# 尝试安装xywechatpad-binary
echo -e "${YELLOW}检查特殊依赖...${NC}"

if [ -d "xywechatpad-binary" ]; then
    echo -e "${GREEN}找到xywechatpad-binary源代码，正在安装...${NC}"
    pip install -e xywechatpad-binary
    echo -e "${GREEN}xywechatpad-binary安装完成${NC}"
elif [ -d "wheels" ]; then
    WHEEL_FILE=$(find wheels -name 'xywechatpad-binary*.whl' 2>/dev/null)
    if [ -n "$WHEEL_FILE" ]; then
        echo -e "${GREEN}找到xywechatpad-binary wheel文件，正在安装...${NC}"
        pip install $WHEEL_FILE
        echo -e "${GREEN}xywechatpad-binary安装完成${NC}"
    else
        echo -e "${RED}未找到xywechatpad-binary wheel文件${NC}"
    fi
else
    echo -e "${RED}未找到xywechatpad-binary，微信API功能将不可用${NC}"
fi

echo -e "${GREEN}依赖安装完成!${NC}" 