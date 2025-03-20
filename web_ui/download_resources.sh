#!/bin/bash

# 设置目录
VENDOR_DIR="web_ui/static/vendor"

# 确保目录存在
mkdir -p $VENDOR_DIR

# 显示彩色输出的函数
function print_success() {
    echo -e "\033[32m[成功]\033[0m $1"
}

function print_error() {
    echo -e "\033[31m[错误]\033[0m $1"
}

function print_info() {
    echo -e "\033[34m[信息]\033[0m $1"
}

# 下载文件并验证
function download_file() {
    local url=$1
    local output=$2
    local file_name=$(basename $output)
    local backup_url=$3

    print_info "正在下载 $file_name..."
    
    # 尝试从主要URL下载
    curl -s -o $output $url
    
    # 检查下载是否成功
    if [ -f "$output" ] && [ -s "$output" ]; then
        print_success "$file_name 下载成功"
        return 0
    else
        print_error "$file_name 从主要来源下载失败"
        
        # 如果有备用URL，尝试从备用URL下载
        if [ ! -z "$backup_url" ]; then
            print_info "尝试从备用来源下载 $file_name..."
            curl -s -o $output $backup_url
            
            if [ -f "$output" ] && [ -s "$output" ]; then
                print_success "$file_name 从备用来源下载成功"
                return 0
            else
                print_error "$file_name 从备用来源下载也失败了"
                return 1
            fi
        fi
        
        return 1
    fi
}

# 如果文件已存在但无法访问，尝试修复权限
function check_and_fix_permissions() {
    local file=$1
    if [ -f "$file" ] && [ ! -r "$file" ]; then
        print_info "尝试修复 $file 的权限..."
        chmod 644 $file
        if [ -r "$file" ]; then
            print_success "权限修复成功"
        else
            print_error "无法修复权限，可能需要管理员权限"
        fi
    fi
}

# 下载主要资源
print_info "开始下载前端资源..."

# Vue.js
download_file "https://gitee.com/mirrors/vue/raw/v3.3.4/dist/vue.global.prod.js" \
              "$VENDOR_DIR/vue.global.min.js" \
              "https://cdn.bootcdn.net/ajax/libs/vue/3.3.4/vue.global.prod.js"

# Element Plus
download_file "https://gitee.com/mianmian-yu/element-plus/raw/2.3.14/dist/index.full.min.js" \
              "$VENDOR_DIR/element-plus.full.min.js" \
              "https://cdn.bootcdn.net/ajax/libs/element-plus/2.3.14/index.full.min.js"

download_file "https://gitee.com/mianmian-yu/element-plus/raw/2.3.14/dist/index.min.css" \
              "$VENDOR_DIR/element-plus.min.css" \
              "https://cdn.bootcdn.net/ajax/libs/element-plus/2.3.14/index.min.css"

# Axios
download_file "https://gitee.com/mirrors/axios/raw/v1.4.0/dist/axios.min.js" \
              "$VENDOR_DIR/axios.min.js" \
              "https://cdn.bootcdn.net/ajax/libs/axios/1.4.0/axios.min.js"

# ECharts
download_file "https://gitee.com/apache/incubator-echarts/raw/5.4.2/dist/echarts.min.js" \
              "$VENDOR_DIR/echarts.min.js" \
              "https://cdn.bootcdn.net/ajax/libs/echarts/5.4.2/echarts.min.js"

# 检查文件和权限
print_info "检查下载的文件..."
for file in vue.global.min.js element-plus.full.min.js element-plus.min.css axios.min.js echarts.min.js; do
    full_path="$VENDOR_DIR/$file"
    if [ -f "$full_path" ] && [ -s "$full_path" ]; then
        print_success "$file 文件存在且非空"
        check_and_fix_permissions "$full_path"
    else
        print_error "$file 文件不存在或为空"
    fi
done

print_info "资源下载完成，请刷新页面查看效果" 