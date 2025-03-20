/**
 * 资源加载器 - 用于处理前端资源加载问题
 */
(function() {
    // 记录需要加载的资源
    const REQUIRED_RESOURCES = [
        { name: 'Vue', 
          paths: ['/static/vendor/vue.global.min.js', '/static/vendor/vue.min.js'],
          global: 'Vue',
          fallback: '/static/vendor/minimal-vue.js' 
        },
        { name: 'ElementPlus', 
          paths: ['/static/vendor/element-plus.full.min.js', '/static/vendor/element-plus.min.js'],
          global: 'ElementPlus',
          fallback: null
        },
        { name: 'axios', 
          paths: ['/static/vendor/axios.min.js'],
          global: 'axios',
          fallback: null
        },
        { name: 'echarts', 
          paths: ['/static/vendor/echarts.min.js'],
          global: 'echarts',
          fallback: '/static/js/fallback-charts.js'
        }
    ];
    
    // 资源加载函数
    function loadResource(resource, callback) {
        // 如果资源已经加载，直接回调
        if (window[resource.global]) {
            console.log(`${resource.name} 已加载`);
            callback(true);
            return;
        }
        
        // 尝试所有可能的路径
        let loadAttempt = 0;
        
        function tryNextPath() {
            if (loadAttempt >= resource.paths.length) {
                // 所有路径都尝试过了，尝试fallback
                if (resource.fallback) {
                    console.warn(`${resource.name} 加载失败，尝试备用方案: ${resource.fallback}`);
                    loadScript(resource.fallback, function(success) {
                        callback(success);
                    });
                } else {
                    console.error(`${resource.name} 加载失败，没有备用方案`);
                    callback(false);
                }
                return;
            }
            
            const path = resource.paths[loadAttempt++];
            loadScript(path, function(success) {
                if (success) {
                    console.log(`${resource.name} 从 ${path} 加载成功`);
                    callback(true);
                } else {
                    console.warn(`${resource.name} 从 ${path} 加载失败，尝试下一个路径`);
                    tryNextPath();
                }
            });
        }
        
        // 开始尝试第一个路径
        tryNextPath();
    }
    
    // 辅助函数：加载脚本
    function loadScript(url, callback) {
        const script = document.createElement('script');
        script.type = 'text/javascript';
        script.src = url;
        
        script.onload = function() {
            callback(true);
        };
        
        script.onerror = function() {
            callback(false);
        };
        
        document.head.appendChild(script);
    }
    
    // 依次加载所有资源
    function loadResourcesSequentially(resources, index, onComplete) {
        if (index >= resources.length) {
            onComplete();
            return;
        }
        
        loadResource(resources[index], function() {
            // 无论成功或失败，继续加载下一个资源
            loadResourcesSequentially(resources, index + 1, onComplete);
        });
    }
    
    // 导出到全局
    window.ResourceLoader = {
        loadAll: function(onComplete) {
            loadResourcesSequentially(REQUIRED_RESOURCES, 0, onComplete);
        }
    };
    
    // 检测DOM加载完成后初始化
    document.addEventListener('DOMContentLoaded', function() {
        // 创建加载提示
        const loadingIndicator = document.createElement('div');
        loadingIndicator.id = 'resource-loading-indicator';
        loadingIndicator.style.position = 'fixed';
        loadingIndicator.style.top = '50%';
        loadingIndicator.style.left = '50%';
        loadingIndicator.style.transform = 'translate(-50%, -50%)';
        loadingIndicator.style.background = 'rgba(255,255,255,0.9)';
        loadingIndicator.style.padding = '20px';
        loadingIndicator.style.borderRadius = '5px';
        loadingIndicator.style.boxShadow = '0 2px 12px rgba(0,0,0,0.1)';
        loadingIndicator.style.zIndex = '9999';
        loadingIndicator.innerHTML = `
            <div style="text-align:center">
                <div style="margin-bottom:10px">正在加载资源...</div>
                <div style="width:50px;height:50px;border:3px solid #f3f3f3;
                          border-top:3px solid #3498db;border-radius:50%;
                          margin:0 auto;animation:spin 1s linear infinite"></div>
            </div>
            <style>
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            </style>
        `;
        document.body.appendChild(loadingIndicator);
        
        // 加载所有资源
        window.ResourceLoader.loadAll(function() {
            // 移除加载提示
            document.body.removeChild(loadingIndicator);
        });
    });
})(); 