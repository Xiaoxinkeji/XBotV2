/**
 * 资源诊断工具 - 检查前端资源加载情况
 */
window.ResourceDiagnostic = {
    // 检查所有关键资源
    checkAllResources: function(callback) {
        const resources = [
            { name: 'Vue.js', path: '/static/vendor/vue.min.js', altPath: '/static/vendor/vue.global.min.js' },
            { name: 'Element Plus JS', path: '/static/vendor/element-plus.min.js', altPath: '/static/vendor/element-plus.full.min.js' },
            { name: 'Element Plus CSS', path: '/static/vendor/element-plus.min.css' },
            { name: 'Axios', path: '/static/vendor/axios.min.js' },
            { name: 'ECharts', path: '/static/vendor/echarts.min.js' },
            { name: '组件脚本', path: '/static/js/main.js' }
        ];
        
        const results = [];
        let pending = resources.length;
        
        resources.forEach(resource => {
            this.checkResource(resource.path, (mainStatus) => {
                // 如果主路径加载失败但有备用路径，检查备用路径
                if (mainStatus === 'error' && resource.altPath) {
                    this.checkResource(resource.altPath, (altStatus) => {
                        results.push({
                            name: resource.name,
                            path: resource.path,
                            altPath: resource.altPath,
                            status: altStatus === 'success' ? 'success' : 'error',
                            mainStatus: mainStatus,
                            altStatus: altStatus
                        });
                        
                        if (--pending === 0) callback(results);
                    });
                } else {
                    results.push({
                        name: resource.name,
                        path: resource.path,
                        status: mainStatus
                    });
                    
                    if (--pending === 0) callback(results);
                }
            });
        });
    },
    
    // 检查单个资源
    checkResource: function(path, callback) {
        const isCSS = path.endsWith('.css');
        
        if (isCSS) {
            // 检查CSS文件
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = path;
            
            link.onload = function() {
                callback('success');
                document.head.removeChild(link);
            };
            
            link.onerror = function() {
                callback('error');
                document.head.removeChild(link);
            };
            
            document.head.appendChild(link);
        } else {
            // 检查JS文件
            const script = document.createElement('script');
            script.type = 'text/javascript';
            script.src = path;
            
            script.onload = function() {
                callback('success');
                document.head.removeChild(script);
            };
            
            script.onerror = function() {
                callback('error');
                document.head.removeChild(script);
            };
            
            document.head.appendChild(script);
        }
    },
    
    // 提供修复建议
    getFixSuggestions: function(results) {
        const failedResources = results.filter(r => r.status === 'error');
        const suggestions = [];
        
        if (failedResources.length === 0) {
            suggestions.push("所有资源检查正常。如果页面仍有问题，可能是JavaScript执行错误。");
            suggestions.push("尝试清除浏览器缓存后重新加载页面。");
            return suggestions;
        }
        
        // 检查是否所有本地资源都无法访问
        const allLocalFailed = failedResources.every(r => r.path.startsWith('/static/'));
        if (allLocalFailed) {
            suggestions.push("多个静态资源无法访问，可能是以下原因:");
            suggestions.push("1. 静态文件目录权限问题 - 请检查web_ui/static目录的权限");
            suggestions.push("2. 静态文件服务配置错误 - 请检查FastAPI的静态文件挂载配置");
            suggestions.push("3. 文件路径不一致 - 实际文件名与代码引用的不一致");
            suggestions.push("运行以下命令修复文件路径不一致问题:");
            suggestions.push("docker exec 容器ID bash /app/web_ui/fix_resources.sh");
        }
        
        // 具体资源建议
        if (failedResources.some(r => r.name === 'Vue.js')) {
            suggestions.push("Vue.js加载失败 - 请检查文件命名是否为vue.min.js或vue.global.min.js");
        }
        
        if (failedResources.some(r => r.name === 'Element Plus JS')) {
            suggestions.push("Element Plus加载失败 - 请检查文件命名是否为element-plus.min.js或element-plus.full.min.js");
        }
        
        if (failedResources.some(r => r.name === 'ECharts')) {
            suggestions.push("ECharts加载失败 - 这会影响图表显示");
        }
        
        // 添加可行的解决方案
        suggestions.push("推荐解决方案: 在容器内运行资源修复脚本");
        suggestions.push("docker exec 容器ID bash -c \"cd /app && bash web_ui/fix_resources.sh\"");
        
        return suggestions;
    }
}; 