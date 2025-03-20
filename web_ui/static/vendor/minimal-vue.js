// 极简版Vue实现，用于应急
window.Vue = {
    version: 'minimal-1.0',
    createApp(options) {
        const app = {
            _options: options,
            _container: null,
            mount(selector) {
                const container = document.querySelector(selector);
                this._container = container;
                
                // 清空容器
                container.innerHTML = '';
                
                // 创建基本结构
                const appContainer = document.createElement('div');
                appContainer.className = 'minimal-app';
                
                const header = document.createElement('header');
                header.className = 'app-header';
                header.innerHTML = '<h1>XYBot管理面板(极简版)</h1>';
                
                const mainContent = document.createElement('div');
                mainContent.className = 'main-content';
                mainContent.innerHTML = `
                    <h2>前端资源加载失败</h2>
                    <p>系统无法加载前端依赖库，正在使用极简备用模式。</p>
                    <div class="card-container">
                        <div class="stat-card">
                            <h3>系统状态</h3>
                            <div class="stat-value">正在运行</div>
                        </div>
                    </div>
                    <p>请检查网络连接或联系管理员。<button id="refresh-btn">刷新页面</button></p>
                `;
                
                appContainer.appendChild(header);
                appContainer.appendChild(mainContent);
                container.appendChild(appContainer);
                
                // 添加简单的事件处理
                document.getElementById('refresh-btn').addEventListener('click', () => {
                    window.location.reload();
                });
                
                return this;
            },
            use() {
                return this; // 支持链式调用
            }
        };
        return app;
    }
};

// 极简ElementPlus模拟
window.ElementPlus = {
    ElMessage: {
        success(msg) {
            alert('成功: ' + msg);
        },
        error(msg) {
            alert('错误: ' + msg);
        }
    }
};

// 极简Axios模拟
window.axios = {
    get(url) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open('GET', url);
            xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve({
                        data: JSON.parse(xhr.responseText),
                        status: xhr.status
                    });
                } else {
                    reject({
                        status: xhr.status,
                        statusText: xhr.statusText
                    });
                }
            };
            xhr.onerror = () => {
                reject({
                    status: xhr.status,
                    statusText: xhr.statusText
                });
            };
            xhr.send();
        });
    }
};

console.log('极简前端库加载完成 - 应急模式'); 