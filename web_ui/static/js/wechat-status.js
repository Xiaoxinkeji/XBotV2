/**
 * 微信服务状态处理
 */
const WechatStatusManager = {
    // 状态常量
    STATUS: {
        CONNECTED: '已连接',
        DISCONNECTED: '未连接',
        RECONNECTING: '重连中...',
        ERROR: '错误'
    },
    
    // 当前状态
    currentStatus: null,
    
    // 自动重试配置
    autoRetry: {
        enabled: true,
        interval: 30000, // 30秒
        maxAttempts: 5,
        attempts: 0,
        timer: null
    },
    
    // 初始化
    init() {
        // 立即检查一次状态
        this.checkStatus();
        
        // 设置定期检查
        setInterval(() => this.checkStatus(), 60000); // 每分钟检查一次
        
        // 添加手动刷新按钮事件处理
        const refreshBtn = document.getElementById('refresh-status-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.checkStatus(true));
        }
    },
    
    // 检查微信状态
    async checkStatus(isManualCheck = false) {
        try {
            // 如果是手动检查，显示加载状态
            if (isManualCheck) {
                this.updateStatusDisplay(null, 'checking');
            }
            
            const response = await fetch('/api/status');
            const data = await response.json();
            
            if (data && data.data && data.data.services) {
                // 更新状态显示
                const wechatStatus = data.data.services.wechat_api;
                this.updateStatusDisplay(wechatStatus);
                
                // 如果之前处于断开状态且现在已连接，重置重试计数
                if (this.currentStatus === this.STATUS.DISCONNECTED && wechatStatus) {
                    this.autoRetry.attempts = 0;
                    if (this.autoRetry.timer) {
                        clearTimeout(this.autoRetry.timer);
                        this.autoRetry.timer = null;
                    }
                }
                
                // 如果当前断开且启用了自动重试，开始重试
                if (!wechatStatus && this.autoRetry.enabled && !this.autoRetry.timer) {
                    this.scheduleRetry();
                }
            }
        } catch (error) {
            console.error('检查微信状态时出错:', error);
            this.updateStatusDisplay(false, 'error');
            
            // 出错时也尝试重试
            if (this.autoRetry.enabled && !this.autoRetry.timer) {
                this.scheduleRetry();
            }
        }
    },
    
    // 更新状态显示
    updateStatusDisplay(connected, special = null) {
        const statusElement = document.getElementById('wechat-status');
        if (!statusElement) return;
        
        // 保存当前状态用于比较
        const prevStatus = this.currentStatus;
        
        // 根据状态设置显示
        if (special === 'checking') {
            statusElement.textContent = '检查中...';
            statusElement.className = 'status-checking';
            this.currentStatus = 'checking';
        } else if (special === 'error') {
            statusElement.textContent = this.STATUS.ERROR;
            statusElement.className = 'status-error';
            this.currentStatus = this.STATUS.ERROR;
        } else if (special === 'reconnecting') {
            statusElement.textContent = this.STATUS.RECONNECTING;
            statusElement.className = 'status-reconnecting';
            this.currentStatus = this.STATUS.RECONNECTING;
        } else if (connected) {
            statusElement.textContent = this.STATUS.CONNECTED;
            statusElement.className = 'status-connected';
            this.currentStatus = this.STATUS.CONNECTED;
        } else {
            statusElement.textContent = this.STATUS.DISCONNECTED;
            statusElement.className = 'status-disconnected';
            this.currentStatus = this.STATUS.DISCONNECTED;
        }
        
        // 如果状态发生变化，触发状态变化事件
        if (prevStatus !== this.currentStatus) {
            this.onStatusChange(this.currentStatus, prevStatus);
        }
    },
    
    // 状态变化处理
    onStatusChange(newStatus, oldStatus) {
        console.log(`微信状态从 ${oldStatus} 变为 ${newStatus}`);
        
        // 如果使用了Element Plus，可以显示通知
        if (window.ElementPlus && window.ElementPlus.ElMessage) {
            if (newStatus === this.STATUS.CONNECTED && oldStatus !== null && oldStatus !== 'checking') {
                ElementPlus.ElMessage.success('微信服务已连接');
            } else if (newStatus === this.STATUS.DISCONNECTED && oldStatus === this.STATUS.CONNECTED) {
                ElementPlus.ElMessage.warning('微信服务已断开');
            }
        }
        
        // 触发自定义事件
        document.dispatchEvent(new CustomEvent('wechatStatusChange', {
            detail: { newStatus, oldStatus }
        }));
    },
    
    // 安排重试
    scheduleRetry() {
        if (this.autoRetry.attempts >= this.autoRetry.maxAttempts) {
            console.log('已达到最大重试次数，停止自动重试');
            return;
        }
        
        this.autoRetry.attempts++;
        
        // 计算重试间隔（可以实现指数退避）
        const retryInterval = this.autoRetry.interval * Math.min(2, this.autoRetry.attempts / 2);
        
        console.log(`安排在 ${retryInterval/1000} 秒后进行第 ${this.autoRetry.attempts} 次重试`);
        
        // 设置重试状态
        this.updateStatusDisplay(false, 'reconnecting');
        
        // 安排重试
        this.autoRetry.timer = setTimeout(() => {
            this.autoRetry.timer = null;
            console.log(`执行第 ${this.autoRetry.attempts} 次重试`);
            this.checkStatus(true);
        }, retryInterval);
    },
    
    // 手动重连微信服务
    async reconnectService() {
        try {
            this.updateStatusDisplay(false, 'reconnecting');
            
            const response = await fetch('/api/wechat/reconnect', {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.code === 200) {
                // 重连指令发送成功，等待并检查状态
                setTimeout(() => this.checkStatus(true), 5000);
                return true;
            } else {
                console.error('发送微信重连指令失败:', result.message);
                this.updateStatusDisplay(false);
                return false;
            }
        } catch (error) {
            console.error('发送微信重连指令时出错:', error);
            this.updateStatusDisplay(false, 'error');
            return false;
        }
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    WechatStatusManager.init();
}); 