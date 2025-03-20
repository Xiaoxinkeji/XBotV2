#!/bin/bash

# 设置资源目录
VENDOR_DIR="/app/web_ui/static/vendor"
echo "正在检查前端资源..."

# 确保目录存在
if [ ! -d "$VENDOR_DIR" ]; then
    echo "创建vendor目录"
    mkdir -p "$VENDOR_DIR"
fi

cd "$VENDOR_DIR" || exit 1

# 函数：检查并创建符号链接
create_symlink() {
    local source=$1
    local target=$2
    
    if [ -f "$source" ] && [ ! -f "$target" ]; then
        echo "创建符号链接: $source -> $target"
        ln -sf "$source" "$target"
    elif [ ! -f "$source" ] && [ -f "$target" ]; then
        echo "创建反向符号链接: $target -> $source"
        ln -sf "$target" "$source"
    elif [ ! -f "$source" ] && [ ! -f "$target" ]; then
        echo "警告: $source 和 $target 都不存在"
    fi
}

# 函数：下载文件如果不存在
download_if_missing() {
    local file=$1
    local url=$2
    local fallback_url=$3
    
    if [ ! -f "$file" ]; then
        echo "下载缺失的文件: $file"
        curl -s -o "$file" "$url" || curl -s -o "$file" "$fallback_url" || echo "警告: $file 下载失败"
    fi
}

# 检查Vue文件
create_symlink "vue.min.js" "vue.global.min.js"

# 检查Element Plus文件
create_symlink "element-plus.min.js" "element-plus.full.min.js"

# 检查并下载echarts
download_if_missing "echarts.min.js" \
    "https://cdn.jsdelivr.net/npm/echarts@5.4.2/dist/echarts.min.js" \
    "https://cdn.bootcdn.net/ajax/libs/echarts/5.4.2/echarts.min.js"

# 下载缺失的核心文件
download_if_missing "vue.min.js" \
    "https://cdn.jsdelivr.net/npm/vue@3.3.4/dist/vue.global.prod.js" \
    "https://cdn.bootcdn.net/ajax/libs/vue/3.3.4/vue.global.prod.js"

download_if_missing "element-plus.min.js" \
    "https://cdn.jsdelivr.net/npm/element-plus@2.3.14/dist/index.full.min.js" \
    "https://cdn.bootcdn.net/ajax/libs/element-plus/2.3.14/index.full.min.js"

download_if_missing "element-plus.min.css" \
    "https://cdn.jsdelivr.net/npm/element-plus@2.3.14/dist/index.min.css" \
    "https://cdn.bootcdn.net/ajax/libs/element-plus/2.3.14/index.min.css"

download_if_missing "axios.min.js" \
    "https://cdn.jsdelivr.net/npm/axios@1.4.0/dist/axios.min.js" \
    "https://cdn.bootcdn.net/ajax/libs/axios/1.4.0/axios.min.js"

# 创建备用实现，以防下载失败
if [ ! -s "vue.min.js" ] && [ ! -s "vue.global.min.js" ]; then
    echo "创建Vue备用实现"
    cat > "vue.min.js" << 'EOF'
// Vue占位实现
window.Vue = {
  createApp(options) {
    console.warn('使用Vue占位实现');
    return {
      use() { return this; },
      component() { return this; },
      mount(selector) {
        const el = document.querySelector(selector);
        if (el) {
          el.innerHTML = '<div style="padding:20px;text-align:center;"><h2>资源加载受限</h2><p>Vue.js未能正确加载，请使用<a href="/simple">简易版</a>或<a href="/offline">诊断工具</a></p></div>';
        }
        return this;
      }
    };
  }
};
EOF
    # 创建符号链接
    ln -sf "vue.min.js" "vue.global.min.js"
fi

# 设置正确的权限
echo "设置文件权限"
chmod 644 *.js *.css 2>/dev/null || true

echo "资源文件修复完成" 