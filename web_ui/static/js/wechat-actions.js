/**
 * 微信操作功能
 */
const WechatActions = {
    // 初始化
    init() {
        // 添加重连按钮事件处理
        const reconnectBtn = document.getElementById('wechat-reconnect-btn');
        if (reconnectBtn) {
            reconnectBtn.addEventListener('click', () => this.reconnectWechatService());
        }
        
        // 监听微信状态变化
        document.addEventListener('wechatStatusChange', (event) => {
            this.onWechatStatusChange(event.detail.newStatus, event.detail.oldStatus);
        });
    },
    
    // 当微信状态变化时的处理
    onWechatStatusChange(newStatus, oldStatus) {
        // 显示或隐藏重连按钮
        const reconnectBtn = document.getElementById('wechat-reconnect-btn');
        if (reconnectBtn) {
            if (newStatus === 'disconnected' || newStatus === 'error') {
                reconnectBtn.style.display = 'inline-block';
            } else {
                reconnectBtn.style.display = 'none';
            }
        }
    },
    
    // 重连微信服务
    async reconnectWechatService() {
        try {
            // 显示加载状态
            const statusElement = document.getElementById('wechat-status');
            if (statusElement) {
                statusElement.textContent = '重连中...';
                statusElement.className = 'status-reconnecting';
            }
            
            // 禁用重连按钮
            const reconnectBtn = document.getElementById('wechat-reconnect-btn');
            if (reconnectBtn) {
                reconnectBtn.disabled = true;
                reconnectBtn.textContent = '重连中...';
            }
            
            // 发送重连请求
            const response = await fetch('/api/wechat/reconnect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            // 恢复按钮状态
            if (reconnectBtn) {
                reconnectBtn.disabled = false;
                reconnectBtn.textContent = '重新连接';
            }
            
            // 处理结果
            if (result.code === 200) {
                // 显示成功消息
                if (window.ElementPlus && window.ElementPlus.ElMessage) {
                    ElementPlus.ElMessage.success('重连指令已发送，正在重新启动微信服务...');
                }
                
                // 5秒后检查状态
                setTimeout(() => {
                    // 触发状态检查
                    if (window.WechatStatusManager) {
                        window.WechatStatusManager.checkStatus(true);
                    }
                }, 5000);
                
                return true;
            } else {
                // 显示错误消息
                if (window.ElementPlus && window.ElementPlus.ElMessage) {
                    ElementPlus.ElMessage.error(`重连失败: ${result.message}`);
                }
                
                // 更新状态显示
                if (statusElement) {
                    statusElement.textContent = '未连接';
                    statusElement.className = 'status-disconnected';
                }
                
                return false;
            }
        } catch (error) {
            console.error('重连微信服务时出错:', error);
            
            // 恢复按钮状态
            const reconnectBtn = document.getElementById('wechat-reconnect-btn');
            if (reconnectBtn) {
                reconnectBtn.disabled = false;
                reconnectBtn.textContent = '重新连接';
            }
            
            // 显示错误状态
            const statusElement = document.getElementById('wechat-status');
            if (statusElement) {
                statusElement.textContent = '错误';
                statusElement.className = 'status-error';
            }
            
            // 显示错误消息
            if (window.ElementPlus && window.ElementPlus.ElMessage) {
                ElementPlus.ElMessage.error(`重连出错: ${error.message}`);
            }
            
            return false;
        }
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    WechatActions.init();
}); 