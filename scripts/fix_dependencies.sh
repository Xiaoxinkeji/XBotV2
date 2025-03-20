#!/bin/bash

# 设置颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}开始检查项目依赖...${NC}"

# 检查requirements.txt是否存在已知问题
if grep -q "matplotlib~=3.10.0" requirements.txt; then
    echo -e "${YELLOW}检测到不兼容的matplotlib版本，正在修复...${NC}"
    sed -i 's/matplotlib~=3.10.0/matplotlib~=3.9.0/g' requirements.txt
    echo -e "${GREEN}已修复 matplotlib 版本要求${NC}"
fi

if grep -q "pysilk>=0.5" requirements.txt; then
    echo -e "${YELLOW}检测到不兼容的pysilk版本，正在修复...${NC}"
    sed -i 's/pysilk>=0.5/pysilk-mod>=1.6.4/g' requirements.txt
    echo -e "${GREEN}已修复 pysilk 版本要求${NC}"
fi

if grep -q "xywechatpad-binary" requirements.txt; then
    echo -e "${YELLOW}检测到特殊依赖 xywechatpad-binary，将单独处理...${NC}"
fi

# 检查是否有其他潜在问题的包
echo -e "${YELLOW}检查其他依赖问题...${NC}"

# 如果存在检查脚本，则运行它
if [ -f "scripts/check_requirements.py" ]; then
    python scripts/check_requirements.py
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}检测到依赖问题，请查看上面的输出并手动修复${NC}"
    fi
else
    echo -e "${YELLOW}未找到依赖检查脚本，跳过详细检查${NC}"
fi

# 生成干净的要求文件
echo -e "${YELLOW}生成过滤后的依赖文件...${NC}"
grep -v -E "xywechatpad-binary|matplotlib~=3.10.0|pysilk>=0.5" requirements.txt > requirements_filtered.txt
echo "matplotlib~=3.9.0" >> requirements_filtered.txt

echo -e "${GREEN}依赖检查和修复完成!${NC}"
echo -e "${YELLOW}现在您可以使用 'pip install -r requirements_filtered.txt' 安装干净的依赖${NC}" 