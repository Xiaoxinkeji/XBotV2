/**
 * XBotV2 通用JavaScript功能
 * 包含所有页面共享的工具函数和全局设置
 */

// 在页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化Bootstrap组件
    initBootstrapComponents();
    
    // 初始化全局事件监听
    initGlobalEventListeners();
});

/**
 * 初始化Bootstrap组件
 */
function initBootstrapComponents() {
    // 初始化tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(tooltipTriggerEl => {
        new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // 初始化popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.forEach(popoverTriggerEl => {
        new bootstrap.Popover(popoverTriggerEl);
    });
    
    // 初始化下拉菜单
    const dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'));
    dropdownElementList.forEach(dropdownToggleEl => {
        new bootstrap.Dropdown(dropdownToggleEl);
    });
}

/**
 * 初始化全局事件监听
 */
function initGlobalEventListeners() {
    // 添加确认对话框
    document.querySelectorAll('[data-confirm]').forEach(el => {
        el.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        });
    });
    
    // 初始化通知容器
    if (!document.querySelector('.notification-container')) {
        const notificationContainer = document.createElement('div');
        notificationContainer.className = 'notification-container';
        document.body.appendChild(notificationContainer);
    }
    
    // 切换可见性的元素
    document.querySelectorAll('[data-toggle-target]').forEach(el => {
        el.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('data-toggle-target'));
            if (target) {
                if (target.style.display === 'none' || getComputedStyle(target).display === 'none') {
                    target.style.display = 'block';
                } else {
                    target.style.display = 'none';
                }
            }
        });
    });
    
    // 处理Active状态
    const currentPath = window.location.pathname;
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
}

/**
 * 显示通知消息
 * @param {string} message - 消息内容
 * @param {string} type - 消息类型 (success, warning, danger, info)
 * @param {number} duration - 显示时长（毫秒）
 */
function showNotification(message, type = 'info', duration = 3000) {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show notification-toast`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="关闭"></button>
    `;
    
    // 添加到页面
    const container = document.querySelector('.notification-container');
    if (container) {
        container.appendChild(notification);
    } else {
        // 如果没有容器，创建一个
        const newContainer = document.createElement('div');
        newContainer.className = 'notification-container';
        document.body.appendChild(newContainer);
        newContainer.appendChild(notification);
    }
    
    // 创建通知的alert对象
    const alert = new bootstrap.Alert(notification);
    
    // 设置自动关闭
    if (duration > 0) {
        setTimeout(() => {
            alert.close();
        }, duration);
    }
    
    // 删除已关闭的通知
    notification.addEventListener('closed.bs.alert', function () {
        notification.remove();
    });
    
    return notification;
}

/**
 * 发送API请求
 * @param {string} url - API地址
 * @param {Object} options - 请求选项
 * @returns {Promise<Object>} - 请求结果
 */
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
    };
    
    const requestOptions = { ...defaultOptions, ...options };
    
    if (requestOptions.body && typeof requestOptions.body === 'object') {
        requestOptions.body = JSON.stringify(requestOptions.body);
    }
    
    try {
        // 添加超时控制
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), options.timeout || 30000);
        requestOptions.signal = controller.signal;
        
        const response = await fetch(url, requestOptions);
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            throw new Error(`HTTP错误: ${response.status}`);
        }
        
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        } else {
            return await response.text();
        }
    } catch (error) {
        console.error('API请求错误:', error);
        
        // 特殊处理超时错误
        if (error.name === 'AbortError') {
            throw new Error('请求超时，请稍后重试');
        }
        
        throw error;
    }
}

/**
 * 格式化日期时间
 * @param {string|Date} date - 日期对象或日期字符串
 * @param {string} format - 格式化模式
 * @returns {string} - 格式化后的日期字符串
 */
function formatDateTime(date, format = 'YYYY-MM-DD HH:mm:ss') {
    if (!date) return '';
    
    const d = typeof date === 'string' ? new Date(date) : date;
    
    if (isNaN(d.getTime())) return '无效日期';
    
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    const seconds = String(d.getSeconds()).padStart(2, '0');
    
    return format
        .replace('YYYY', year)
        .replace('MM', month)
        .replace('DD', day)
        .replace('HH', hours)
        .replace('mm', minutes)
        .replace('ss', seconds);
}

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @param {number} decimals - 小数位数
 * @returns {string} - 格式化后的文件大小
 */
function formatFileSize(bytes, decimals = 2) {
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * 防抖函数
 * @param {Function} func - 需要防抖的函数
 * @param {number} wait - 等待时间（毫秒）
 * @returns {Function} - 防抖处理后的函数
 */
function debounce(func, wait = 300) {
    let timeout;
    return function(...args) {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}

/**
 * 节流函数
 * @param {Function} func - 需要节流的函数
 * @param {number} limit - 时间限制（毫秒）
 * @returns {Function} - 节流处理后的函数
 */
function throttle(func, limit = 300) {
    let inThrottle;
    return function(...args) {
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * 获取URL参数
 * @param {string} name - 参数名
 * @returns {string} - 参数值
 */
function getUrlParameter(name) {
    name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
    const regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
    const results = regex.exec(location.search);
    return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
}

/**
 * 随机字符串生成
 * @param {number} length - 字符串长度
 * @returns {string} - 随机字符串
 */
function randomString(length = 10) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

/**
 * 发送PushPlus通知
 * @param {string} title - 通知标题
 * @param {string} content - 通知内容
 * @param {string} template - 消息模板类型，默认html
 * @returns {Promise<Object>} - 返回发送结果
 */
async function sendPushNotification(title, content, template = 'html') {
    try {
        // 获取通知设置
        const response = await fetch('/api/settings');
        const settings = await response.json();
        
        if (!settings.success || !settings.data.Notification || !settings.data.Notification.enable) {
            console.log('通知功能未启用');
            return { success: false, message: '通知功能未启用' };
        }
        
        const pushplusToken = settings.data.Notification.pushplus_token;
        if (!pushplusToken) {
            console.log('未配置PushPlus token');
            return { success: false, message: '未配置PushPlus token' };
        }
        
        // 构建通知数据
        const notifyData = {
            token: pushplusToken,
            title: title,
            content: content,
            template: template
        };
        
        // 发送请求到PushPlus
        const pushResponse = await fetch('https://www.pushplus.plus/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(notifyData)
        });
        
        const result = await pushResponse.json();
        if (result.code === 200) {
            console.log('通知发送成功:', result);
            return { success: true, message: '通知发送成功', data: result.data };
        } else {
            console.warn('通知发送失败:', result.msg);
            return { success: false, message: `通知发送失败: ${result.msg}` };
        }
    } catch (error) {
        console.error('发送通知时出错:', error);
        return { success: false, message: `发送通知时出错: ${error.message}` };
    }
}

// 导出工具函数
window.XBot = {
    showNotification,
    apiRequest,
    formatDateTime,
    formatFileSize,
    debounce,
    throttle,
    getUrlParameter,
    randomString,
    sendPushNotification
}; 