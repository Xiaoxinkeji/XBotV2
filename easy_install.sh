#!/bin/bash

# 设置颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}XYBot 简易安装脚本${NC}"
echo -e "${YELLOW}此脚本将帮助您安装所有必要依赖${NC}"

# 检查Python版本
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
echo -e "${GREEN}检测到Python版本: ${python_version}${NC}"

# 如果Python版本小于3.9，发出警告
python_major=$(echo $python_version | cut -d'.' -f1)
python_minor=$(echo $python_version | cut -d'.' -f2)

if [ "$python_major" -lt 3 ] || ([ "$python_major" -eq 3 ] && [ "$python_minor" -lt 9 ]); then
    echo -e "${RED}警告: 推荐使用Python 3.9或更高版本${NC}"
    read -p "是否继续? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 更新pip
echo -e "${YELLOW}更新pip...${NC}"
python3 -m pip install --upgrade pip

# 使用依赖管理工具修复和安装依赖
if [ -f "scripts/manage_dependencies.py" ]; then
    echo -e "${YELLOW}使用依赖管理工具...${NC}"
    python3 scripts/manage_dependencies.py --fix --output requirements_fixed.txt
    
    echo -e "${YELLOW}安装修复后的依赖...${NC}"
    python3 -m pip install -r requirements_fixed.txt
else
    echo -e "${YELLOW}使用基本依赖过滤...${NC}"
    grep -v -E "matplotlib~=3.10.0|pysilk>=0.5" requirements.txt > requirements_filtered.txt
    echo "matplotlib~=3.9.0" >> requirements_filtered.txt
    echo "pysilk-mod>=1.6.4" >> requirements_filtered.txt
    
    echo -e "${YELLOW}安装过滤后的依赖...${NC}"
    python3 -m pip install -r requirements_filtered.txt
fi

# 尝试安装xywechatpad-binary
echo -e "${YELLOW}检查特殊依赖...${NC}"

# 首先尝试直接安装
echo -e "${YELLOW}尝试从PyPI安装xywechatpad-binary...${NC}"
if pip install xywechatpad-binary==1.1.0; then
    echo -e "${GREEN}成功安装xywechatpad-binary${NC}"
elif
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
        echo -e "${YELLOW}微信API功能将不可用${NC}"
    fi
else
    echo -e "${RED}未找到xywechatpad-binary，微信API功能将不可用${NC}"
fi

# 安装完成提示
echo -e "${GREEN}安装完成!${NC}"

# 检查端口配置
if [ -f "scripts/check_port_config.py" ]; then
    echo -e "${YELLOW}检查端口配置...${NC}"
    python3 scripts/check_port_config.py
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}⚠️ 端口配置可能不一致，请检查上面的警告${NC}"
    else
        echo -e "${GREEN}✅ 端口配置一致${NC}"
    fi
fi

echo -e "${YELLOW}现在您可以运行 'python3 main.py' 启动应用${NC}" 