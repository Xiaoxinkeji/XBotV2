/**
 * XBotV2 首页仪表盘交互脚本
 * 实现机器人状态更新、图表显示和响应式交互功能
 */

// 全局变量
let statsChart = null;
let statusRefreshInterval = null;

// 存储上一次的机器人状态
let lastRobotStatus = null;

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function () {
    // 初始化状态刷新
    initStatusRefresh();
    
    // 初始化图表
    initStatsChart();
    
    // 绑定图表周期切换事件
    initChartPeriodButtons();
    
    // 绑定日志过滤事件
    initLogFiltering();
    
    // 初始化按钮事件
    initControlButtons();
    
    // 页面卸载前清除所有定时器
    window.addEventListener('beforeunload', function() {
        if (statusRefreshInterval) clearInterval(statusRefreshInterval);
    });
});

/**
 * 初始化状态刷新
 */
function initStatusRefresh() {
    // 立即获取一次状态
    refreshStatus();
    
    // 设置定时刷新 (每30秒)
    statusRefreshInterval = setInterval(refreshStatus, 30000);
}

/**
 * 刷新机器人和系统状态
 */
async function refreshStatus() {
    try {
        // 添加超时控制
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10秒超时
        
        const response = await fetch('/api/status', {
            signal: controller.signal
        });
        clearTimeout(timeoutId); // 清除超时计时器
        
        if (!response.ok) {
            throw new Error(`HTTP错误: ${response.status}`);
        }
        
        const data = await response.json();
        
        // 更新各种状态信息
        updateRobotStatus(data.robot);
        updateSystemStatus(data.system);
        updatePluginStatus(data.plugins);
        updateMessageStats(data.messages);
        
        // 如果页面上有日志表格和消息表格，则获取更多数据更新它们
        if (document.getElementById('recentMessages')) {
            fetch('/api/messages?limit=5')
                .then(response => response.json())
                .then(data => {
                    if (data.messages) {
                        updateRecentMessages(data.messages);
                    }
                })
                .catch(err => console.error('获取最近消息失败:', err));
        }
        
        if (document.getElementById('recentLogs')) {
            fetch('/api/logs?limit=5')
                .then(response => response.json())
                .then(data => {
                    if (data.logs) {
                        updateRecentLogs(data.logs);
                    }
                })
                .catch(err => console.error('获取最近日志失败:', err));
        }
        
        // 如果有图表并且显示在页面上，则更新图表
        if (statsChart && document.getElementById('statsChart')) {
            // 这里可以使用模拟数据或者从服务器获取真实数据
            updateChartWithMockData('day');
        }
    } catch (error) {
        console.error('刷新状态错误:', error);
        
        // 显示错误信息
        document.getElementById('robotStatus').innerHTML = 
            `<span class="text-danger">获取状态失败</span>`;
        document.getElementById('robotStatusIcon').className = 
            'bi bi-exclamation-triangle-fill text-danger';
        
        // 禁用控制按钮
        document.getElementById('startRobot').disabled = true;
        document.getElementById('stopRobot').disabled = true;
        document.getElementById('restartRobot').disabled = true;
        
        // 如果是超时错误，自动重试一次
        if (error.name === 'AbortError') {
            console.log('状态请求超时，将在5秒后重试');
            setTimeout(() => {
                refreshStatus().catch(e => console.error('重试也失败:', e));
            }, 5000);
        }
    }
}

/**
 * 更新机器人状态
 */
function updateRobotStatus(robotData) {
    if (!robotData) return;
    
    const statusEl = document.getElementById('robotStatus');
    const iconEl = document.getElementById('robotStatusIcon');
    const startBtn = document.getElementById('startRobot');
    const stopBtn = document.getElementById('stopRobot');
    const restartBtn = document.getElementById('restartRobot');
    const detailsDiv = document.getElementById('robotDetails');
    
    // 检查状态是否发生变化
    if (lastRobotStatus !== null) {
        const statusChanged = lastRobotStatus.online !== robotData.online;
        if (statusChanged) {
            // 状态变化，显示通知
            if (robotData.online) {
                // 从离线变为在线
                showNotification('机器人已上线', 'success', 5000);
            } else {
                // 从在线变为离线
                showNotification('机器人已掉线', 'danger', 5000);
            }
        }
    }
    
    // 更新上一次状态
    lastRobotStatus = {...robotData};
    
    if (robotData.online) {
        // 在线状态
        statusEl.innerHTML = `<span class="text-success">在线</span>`;
        iconEl.className = 'bi bi-check-circle-fill text-success status-pulse';
        
        // 启用停止和重启按钮，禁用启动按钮
        startBtn.disabled = true;
        stopBtn.disabled = false;
        restartBtn.disabled = false;
        
        // 显示详细信息
        detailsDiv.style.display = 'block';
        if (document.getElementById('robotPid')) {
            document.getElementById('robotPid').textContent = robotData.pid || '--';
        }
        if (document.getElementById('robotUptime')) {
            document.getElementById('robotUptime').textContent = formatUptime(robotData.uptime) || '--';
        }
        if (document.getElementById('pluginCount')) {
            document.getElementById('pluginCount').textContent = robotData.plugin_count || '0';
        }
        
        // 如果有用户资料，显示用户信息
        if (robotData.wxid && document.getElementById('wxProfile')) {
            const profileDiv = document.getElementById('wxProfile');
            profileDiv.style.display = 'block';
            
            if (document.getElementById('wxNickname')) {
                document.getElementById('wxNickname').textContent = robotData.nickname || robotData.wxid;
            }
            if (document.getElementById('wxId')) {
                document.getElementById('wxId').textContent = robotData.wxid;
            }
            // 如果有头像
            if (robotData.avatar_url && document.getElementById('wxAvatar')) {
                document.getElementById('wxAvatar').src = robotData.avatar_url;
            }
        }
    } else if (robotData.loading) {
        // 加载中状态
        statusEl.innerHTML = `<span class="spinner-border spinner-border-sm me-1" role="status"></span><span class="text-warning">加载中...</span>`;
        iconEl.className = 'bi bi-hourglass-split text-warning';
        
        // 禁用所有按钮
        startBtn.disabled = true;
        stopBtn.disabled = true;
        restartBtn.disabled = true;
        
        // 隐藏详细信息
        detailsDiv.style.display = 'none';
    } else {
        // 离线状态
        statusEl.innerHTML = `<span class="text-danger">离线</span>`;
        iconEl.className = 'bi bi-x-circle-fill text-danger';
        
        // 启用启动按钮，禁用停止和重启按钮
        startBtn.disabled = false;
        stopBtn.disabled = true;
        restartBtn.disabled = true;
        
        // 隐藏详细信息
        detailsDiv.style.display = 'none';
    }
}

/**
 * 更新系统状态
 */
function updateSystemStatus(systemData) {
    if (!systemData) return;
    
    // 更新 CPU 使用率
    const cpuUsage = document.getElementById('cpuUsage');
    const cpuText = document.getElementById('cpuText');
    
    if (cpuUsage && cpuText) {
        const cpuPercent = systemData.cpu || 0;
        cpuUsage.style.width = `${cpuPercent}%`;
        cpuText.textContent = `${cpuPercent}%`;
        
        // 根据使用率调整颜色
        if (cpuPercent > 80) {
            cpuUsage.className = 'progress-bar bg-danger';
        } else if (cpuPercent > 60) {
            cpuUsage.className = 'progress-bar bg-warning';
        } else {
            cpuUsage.className = 'progress-bar bg-info';
        }
    }
    
    // 更新内存使用率
    const memoryUsage = document.getElementById('memoryUsage');
    const memoryText = document.getElementById('memoryText');
    
    if (memoryUsage && memoryText) {
        // 计算内存使用百分比 (假设最大值为系统总内存)
        const memoryPercent = systemData.memory_percent || 0;
        const memoryMB = (systemData.memory / (1024 * 1024)).toFixed(2);
        
        memoryUsage.style.width = `${memoryPercent}%`;
        memoryText.textContent = `${memoryMB} MB`;
        
        // 根据使用率调整颜色
        if (memoryPercent > 80) {
            memoryUsage.className = 'progress-bar bg-danger';
        } else if (memoryPercent > 60) {
            memoryUsage.className = 'progress-bar bg-warning';
        } else {
            memoryUsage.className = 'progress-bar bg-warning';
        }
    }
    
    // 更新运行时间
    const uptimeEl = document.getElementById('uptime');
    if (uptimeEl) {
        uptimeEl.textContent = formatUptime(systemData.uptime);
    }
}

/**
 * 更新插件状态
 */
function updatePluginStatus(pluginData) {
    if (!pluginData) return;
    
    const totalPlugins = document.getElementById('totalPlugins');
    const enabledPlugins = document.getElementById('enabledPlugins');
    const disabledPlugins = document.getElementById('disabledPlugins');
    
    if (totalPlugins) totalPlugins.textContent = pluginData.total || 0;
    if (enabledPlugins) enabledPlugins.textContent = pluginData.enabled || 0;
    if (disabledPlugins) disabledPlugins.textContent = pluginData.disabled || 0;
}

/**
 * 更新消息统计
 */
function updateMessageStats(messageStats) {
    if (!messageStats) return;
    
    const totalEl = document.getElementById('totalMessages');
    const todayEl = document.getElementById('todayMessages');
    const groupEl = document.getElementById('groupMessages');
    const privateEl = document.getElementById('privateMessages');
    
    if (totalEl) totalEl.textContent = messageStats.total || 0;
    if (todayEl) todayEl.textContent = messageStats.today || 0;
    if (groupEl) groupEl.textContent = messageStats.group || 0;
    if (privateEl) privateEl.textContent = messageStats.private || 0;
}

/**
 * 更新最近消息列表
 */
function updateRecentMessages(messages) {
    const container = document.getElementById('recentMessages');
    if (!container) return;
    
    if (!messages || messages.length === 0) {
        container.innerHTML = `
            <tr>
                <td colspan="4" class="text-center py-3">暂无消息记录</td>
            </tr>
        `;
        return;
    }
    
    container.innerHTML = '';
    
    messages.forEach(msg => {
        const row = document.createElement('tr');
        
        // 消息来源
        const sourceCell = document.createElement('td');
        sourceCell.innerText = msg.sender_name || msg.sender || '未知';
        row.appendChild(sourceCell);
        
        // 消息内容（截断过长内容）
        const contentCell = document.createElement('td');
        const content = msg.content || '';
        contentCell.innerText = content.length > 30 ? content.substring(0, 30) + '...' : content;
        contentCell.title = content; // 完整内容显示为提示
        row.appendChild(contentCell);
        
        // 消息类型（在小屏幕上隐藏）
        const typeCell = document.createElement('td');
        typeCell.className = 'hide-sm';
        typeCell.innerText = getMessageTypeName(msg.type);
        row.appendChild(typeCell);
        
        // 时间
        const timeCell = document.createElement('td');
        timeCell.innerText = formatTime(msg.time);
        row.appendChild(timeCell);
        
        container.appendChild(row);
    });
}

/**
 * 更新最近日志列表
 */
function updateRecentLogs(logs) {
    const container = document.getElementById('recentLogs');
    if (!container) return;
    
    if (!logs || logs.length === 0) {
        container.innerHTML = `
            <tr>
                <td colspan="3" class="text-center py-3">暂无日志记录</td>
            </tr>
        `;
        return;
    }
    
    container.innerHTML = '';
    
    logs.forEach(log => {
        const row = document.createElement('tr');
        
        // 日志级别
        const levelCell = document.createElement('td');
        const level = (log.level || 'INFO').toUpperCase();
        let badgeClass = 'bg-info';
        
        switch (level) {
            case 'ERROR':
                badgeClass = 'bg-danger';
                break;
            case 'WARNING':
                badgeClass = 'bg-warning';
                break;
            case 'DEBUG':
                badgeClass = 'bg-secondary';
                break;
        }
        
        levelCell.innerHTML = `<span class="badge ${badgeClass}">${level}</span>`;
        row.appendChild(levelCell);
        
        // 日志内容
        const contentCell = document.createElement('td');
        const content = log.content || log.message || '';
        contentCell.innerText = content.length > 50 ? content.substring(0, 50) + '...' : content;
        contentCell.title = content; // 完整内容显示为提示
        row.appendChild(contentCell);
        
        // 时间（在小屏幕上隐藏）
        const timeCell = document.createElement('td');
        timeCell.className = 'hide-sm';
        timeCell.innerText = formatTime(log.time);
        row.appendChild(timeCell);
        
        container.appendChild(row);
    });
}

/**
 * 初始化数据统计图表
 */
function initStatsChart() {
    const chartContainer = document.getElementById('statsChart');
    if (!chartContainer) return;
    
    // 检查Chart.js是否已加载
    if (typeof Chart === 'undefined') {
        console.error('Chart.js未加载，图表功能不可用');
        return;
    }
    
    try {
        // 创建初始图表（空数据）
        statsChart = new Chart(chartContainer, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: '消息数量',
                    data: [],
                    fill: true,
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    borderColor: 'rgba(13, 110, 253, 0.8)',
                    borderWidth: 2,
                    tension: 0.4,
                    pointBackgroundColor: 'rgba(13, 110, 253, 1)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            precision: 0
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
        
        // 添加一些模拟数据进行演示
        updateChartWithMockData('day');
    } catch (error) {
        console.error('初始化图表失败:', error);
        if (chartContainer.parentNode) {
            chartContainer.parentNode.innerHTML = '<div class="alert alert-warning my-3">图表加载失败</div>';
        }
    }
}

/**
 * 更新统计图表数据
 */
function updateStatsChart(chartData) {
    if (!statsChart || !chartData) return;
    
    try {
        statsChart.data.labels = chartData.labels || [];
        statsChart.data.datasets[0].data = chartData.data || [];
        statsChart.update();
    } catch (error) {
        console.error('更新图表数据失败:', error);
    }
}

/**
 * 使用模拟数据更新图表（仅用于演示）
 */
function updateChartWithMockData(period) {
    if (!statsChart) return;
    
    let labels = [];
    let data = [];
    
    switch (period) {
        case 'day':
            // 生成24小时数据
            for (let i = 0; i < 24; i++) {
                labels.push(`${i}:00`);
                data.push(Math.floor(Math.random() * 30));
            }
            break;
            
        case 'week':
            // 生成7天数据
            const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
            for (let i = 0; i < 7; i++) {
                labels.push(days[i]);
                data.push(Math.floor(Math.random() * 100) + 50);
            }
            break;
            
        case 'month':
            // 生成30天数据
            for (let i = 1; i <= 30; i++) {
                labels.push(`${i}日`);
                data.push(Math.floor(Math.random() * 200) + 100);
            }
            break;
    }
    
    statsChart.data.labels = labels;
    statsChart.data.datasets[0].data = data;
    statsChart.update();
}

/**
 * 初始化图表周期切换按钮
 */
function initChartPeriodButtons() {
    const buttons = document.querySelectorAll('.card-header [data-period]');
    if (!buttons.length) return;
    
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            // 移除所有按钮的活动状态
            buttons.forEach(btn => btn.classList.remove('active'));
            
            // 设置当前按钮为活动状态
            this.classList.add('active');
            
            // 更新图表数据
            const period = this.getAttribute('data-period');
            updateChartWithMockData(period);
        });
    });
}

/**
 * 初始化日志过滤功能
 */
function initLogFiltering() {
    const logLevelSelect = document.getElementById('logLevel');
    if (!logLevelSelect) return;
    
    logLevelSelect.addEventListener('change', function() {
        // 模拟过滤效果（实际实现应当重新请求数据）
        const selectedLevel = this.value;
        console.log(`日志过滤: ${selectedLevel || '全部'}`);
        
        // 这里应当重新刷新日志数据
        // 为简化示例，暂不实现实际过滤功能
    });
}

/**
 * 初始化控制按钮
 */
function initControlButtons() {
    // 启动机器人
    const startBtn = document.getElementById('startRobot');
    const stopBtn = document.getElementById('stopRobot');
    const restartBtn = document.getElementById('restartRobot');
    
    const showMessage = (message, type = 'success') => {
        // 使用通知系统显示消息
        if (typeof showNotification === 'function') {
            showNotification(message, type);
        } else {
            alert(message);
        }
    };
    
    // 通用的控制函数
    const controlRobot = async (action, button, pendingText, successText, errorText) => {
        const originalHTML = button.innerHTML;
        
        try {
            button.disabled = true;
            button.innerHTML = `<span class="spinner-border spinner-border-sm" role="status"></span> ${pendingText}`;
            
            // 进行重试逻辑，最多尝试3次
            let retries = 0;
            const maxRetries = 2;
            let success = false;
            let errorMsg = '';
            
            while (retries <= maxRetries && !success) {
                try {
                    const response = await fetch(`/api/robot/control/${action}`, { 
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });
                    
                    if (!response.ok) {
                        throw new Error(`HTTP错误: ${response.status}`);
                    }
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        success = true;
                        showMessage(successText);
                    } else {
                        throw new Error(data.message || `${action}失败`);
                    }
                } catch (e) {
                    retries++;
                    errorMsg = e.message;
                    if (retries <= maxRetries) {
                        console.log(`重试 ${action}，第${retries}次...`);
                        await new Promise(resolve => setTimeout(resolve, 1000)); // 等待1秒再重试
                    }
                }
            }
            
            if (!success) {
                throw new Error(errorMsg);
            }
            
            // 更新完成后，适当延迟刷新状态，给服务端足够时间改变状态
            const delay = action === 'restart' ? 5000 : 2000;
            
            // 首先执行一次立即刷新，然后延迟后再次刷新
            refreshStatus();
            setTimeout(() => {
                refreshStatus();
                setTimeout(refreshStatus, 1000); // 额外再刷新一次，确保状态正确
            }, delay);
            
        } catch (error) {
            console.error(`${action}机器人错误:`, error);
            showMessage(`${errorText}: ${error.message}`, 'error');
        } finally {
            // 根据操作和当前状态更新按钮的启用/禁用状态
            setTimeout(() => {
                if (action === 'start') {
                    button.innerHTML = originalHTML;
                    // 在刷新状态API调用中会自动设置按钮状态
                } else if (action === 'stop') {
                    button.innerHTML = originalHTML;
                } else if (action === 'restart') {
                    button.innerHTML = originalHTML;
                }
            }, 500);
        }
    };
    
    if (startBtn) {
        startBtn.addEventListener('click', function() {
            if (!confirm('确定要启动机器人吗？')) return;
            controlRobot('start', startBtn, '启动中...', '机器人已成功启动', '启动机器人失败');
        });
    }
    
    if (stopBtn) {
        stopBtn.addEventListener('click', function() {
            if (!confirm('确定要停止机器人吗？这将断开所有当前连接。')) return;
            controlRobot('stop', stopBtn, '停止中...', '机器人已成功停止', '停止机器人失败');
        });
    }
    
    if (restartBtn) {
        restartBtn.addEventListener('click', function() {
            if (!confirm('确定要重启机器人吗？重启过程中机器人将暂时不可用。')) return;
            controlRobot('restart', restartBtn, '重启中...', '机器人已成功重启', '重启机器人失败');
        });
    }
    
    // 添加快捷键支持
    document.addEventListener('keydown', function(e) {
        // 只有在按下Alt键的情况下才处理
        if (e.altKey) {
            if (e.key === 's' && !startBtn.disabled) { // Alt+S 启动
                e.preventDefault();
                startBtn.click();
            } else if (e.key === 'x' && !stopBtn.disabled) { // Alt+X 停止
                e.preventDefault();
                stopBtn.click();
            } else if (e.key === 'r' && !restartBtn.disabled) { // Alt+R 重启
                e.preventDefault();
                restartBtn.click();
            }
        }
    });
}

/**
 * 格式化运行时间
 */
function formatUptime(seconds) {
    if (!seconds && seconds !== 0) return '未知';
    
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    let result = '';
    if (days > 0) result += `${days}天 `;
    if (hours > 0 || days > 0) result += `${hours}小时 `;
    result += `${minutes}分钟`;
    
    return result;
}

/**
 * 格式化时间为友好显示
 */
function formatTime(timestamp) {
    if (!timestamp) return '-';
    
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    
    // 当天内显示时:分
    if (diffMs < 24 * 60 * 60 * 1000 && date.getDate() === now.getDate()) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    // 一周内显示星期几
    if (diffMs < 7 * 24 * 60 * 60 * 1000) {
        const days = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
        return days[date.getDay()] + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    // 其他显示完整日期
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

/**
 * 获取消息类型的显示名称
 */
function getMessageTypeName(type) {
    const types = {
        'text': '文本',
        'image': '图片',
        'voice': '语音',
        'video': '视频',
        'file': '文件',
        'link': '链接',
        'system': '系统',
        'emoji': '表情'
    };
    
    return types[type] || type || '未知';
} 