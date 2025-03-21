/**
 * XBotV2 Web管理界面主要JavaScript文件
 */

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    console.log('XBotV2 Web管理界面已加载');
    
    // 设置活动导航项
    setActiveNavItem();
    
    // 添加通用功能
    setupTooltips();
    setupModalHandlers();
    
    // 处理移动设备上的下拉菜单关闭问题
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    const bsCollapse = new bootstrap.Collapse(navbarCollapse, {toggle: false});
    
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth < 992) { // Bootstrap lg breakpoint
                bsCollapse.hide();
            }
        });
    });
    
    // 根据滚动位置控制返回顶部按钮
    const scrollTopBtn = document.getElementById('scrollTopBtn');
    if (scrollTopBtn) {
        window.addEventListener('scroll', function() {
            if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
                scrollTopBtn.style.display = 'block';
            } else {
                scrollTopBtn.style.display = 'none';
            }
        });
        
        scrollTopBtn.addEventListener('click', function() {
            window.scrollTo({top: 0, behavior: 'smooth'});
        });
    }
    
    // 处理全局的alert自动消失
    const alerts = document.querySelectorAll('.alert:not(.alert-persistent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const closeBtn = alert.querySelector('.btn-close');
            if (closeBtn) {
                closeBtn.click();
            }
        }, 5000);
    });

    // 注册全局确认对话框
    window.confirmAction = function(message, callback) {
        if (confirm(message)) {
            callback();
        }
    };
    
    // 初始化全局工具提示
    initTooltips();
});

/**
 * 设置当前活动的导航项
 */
function setActiveNavItem() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (currentPath === href || (href !== '/' && currentPath.startsWith(href))) {
            link.classList.add('active');
        }
    });
}

/**
 * 设置工具提示
 */
function setupTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * 设置模态框处理器
 */
function setupModalHandlers() {
    // 模态框关闭时清除数据
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('hidden.bs.modal', function() {
            const forms = this.querySelectorAll('form');
            forms.forEach(form => form.reset());
        });
    });
}

/**
 * 通用的API调用函数
 * @param {string} url - API端点
 * @param {string} method - HTTP方法
 * @param {Object} data - 请求数据
 * @returns {Promise} - 返回Promise对象
 */
async function apiCall(url, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (data && (method === 'POST' || method === 'PUT')) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('API调用失败:', error);
        throw error;
    }
}

/**
 * 显示通知消息
 * @param {string} message - 消息内容
 * @param {string} type - 消息类型 (success, danger, warning, info)
 * @param {number} duration - 显示时长(毫秒)
 */
function showNotification(message, type = 'info', duration = 3000) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.top = '20px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '9999';
    alertDiv.style.minWidth = '300px';
    
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // 自动关闭
    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alertDiv);
        bsAlert.close();
    }, duration);
}

/**
 * 格式化日期时间
 * @param {Date|string} date - 日期对象或日期字符串
 * @param {boolean} includeTime - 是否包含时间
 * @returns {string} - 格式化后的日期时间字符串
 */
function formatDateTime(date, includeTime = true) {
    const d = new Date(date);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    
    let result = `${year}-${month}-${day}`;
    
    if (includeTime) {
        const hours = String(d.getHours()).padStart(2, '0');
        const minutes = String(d.getMinutes()).padStart(2, '0');
        const seconds = String(d.getSeconds()).padStart(2, '0');
        result += ` ${hours}:${minutes}:${seconds}`;
    }
    
    return result;
}

/**
 * 初始化Bootstrap工具提示
 */
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            trigger: 'hover'
        });
    });
}

/**
 * 显示提示信息
 * @param {string} message - 消息内容
 * @param {string} type - 消息类型 (success, info, warning, danger)
 * @param {number} duration - 显示时长(毫秒)，0表示不自动关闭
 * @param {string} containerId - 消息容器ID，默认为"alertContainer"
 */
function showAlert(message, type = 'info', duration = 5000, containerId = 'alertContainer') {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Alert container #${containerId} not found.`);
        return;
    }
    
    const alertId = 'alert-' + Date.now();
    const alertHtml = `
        <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="关闭"></button>
        </div>
    `;
    
    container.innerHTML += alertHtml;
    
    if (duration > 0) {
        setTimeout(() => {
            const alert = document.getElementById(alertId);
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, duration);
    }
    
    return alertId;
}

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @param {number} decimals - 小数位数
 * @returns {string} 格式化后的文件大小字符串
 */
function formatFileSize(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * 异步加载数据
 * @param {string} url - API地址
 * @param {Function} successCallback - 成功回调函数
 * @param {Function} errorCallback - 错误回调函数
 * @param {Object} options - 请求选项
 */
async function loadData(url, successCallback, errorCallback, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    const requestOptions = {...defaultOptions, ...options};
    
    try {
        const response = await fetch(url, requestOptions);
        const data = await response.json();
        
        if (data.success) {
            if (typeof successCallback === 'function') {
                successCallback(data);
            }
        } else {
            if (typeof errorCallback === 'function') {
                errorCallback(data.message || '请求失败');
            } else {
                console.error('请求失败:', data.message);
            }
        }
    } catch (error) {
        if (typeof errorCallback === 'function') {
            errorCallback(error.message || '网络错误');
        } else {
            console.error('网络错误:', error);
        }
    }
}

/**
 * 复制文本到剪贴板
 * @param {string} text - 要复制的文本
 * @returns {Promise<boolean>} 是否复制成功
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch (err) {
        console.error('复制到剪贴板失败:', err);
        return false;
    }
}

/**
 * 防抖函数
 * @param {Function} func - 要执行的函数
 * @param {number} wait - 等待时间(毫秒)
 * @returns {Function} 防抖处理后的函数
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
 * @param {Function} func - 要执行的函数
 * @param {number} limit - 限制时间(毫秒)
 * @returns {Function} 节流处理后的函数
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