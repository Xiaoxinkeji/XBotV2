// 面板组件
const ComponentDashboard = {
    data() {
        return {
            loading: true,
            stats: null,
            botStats: null,
            recentMessages: [],
            messageChartData: null
        }
    },
    mounted() {
        this.fetchStats();
        this.fetchRecentMessages();
        
        // 每60秒刷新一次数据
        this.refreshInterval = setInterval(() => {
            this.fetchStats();
        }, 60000);
    },
    beforeUnmount() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
    },
    methods: {
        fetchStats() {
            this.loading = true;
            
            // 获取系统状态
            axios.get('/api/status')
                .then(response => {
                    this.stats = response.data.data;
                    
                    // 获取机器人统计
                    return axios.get('/api/stats');
                })
                .then(response => {
                    this.botStats = response.data.data;
                    
                    // 渲染数据
                    this.$nextTick(() => {
                        this.renderMessageChart();
                    });
                    
                    this.loading = false;
                })
                .catch(error => {
                    console.error('获取统计信息失败:', error);
                    this.$message.error('获取统计信息失败');
                    this.loading = false;
                });
        },
        
        fetchRecentMessages() {
            axios.get('/api/messages?limit=5')
                .then(response => {
                    this.recentMessages = response.data.data;
                })
                .catch(error => {
                    console.error('获取最近消息失败:', error);
                });
        },
        
        renderMessageChart() {
            if (!this.botStats || !this.botStats.daily_message_count) return;
            
            const chart = echarts.init(document.getElementById('message-trend-chart'));
            
            const dates = this.botStats.daily_message_count.map(item => item.date);
            const counts = this.botStats.daily_message_count.map(item => item.count);
            
            chart.setOption({
                title: {
                    text: '消息趋势'
                },
                tooltip: {
                    trigger: 'axis'
                },
                xAxis: {
                    type: 'category',
                    data: dates
                },
                yAxis: {
                    type: 'value'
                },
                series: [{
                    data: counts,
                    type: 'line',
                    smooth: true,
                    areaStyle: {
                        opacity: 0.2
                    },
                    itemStyle: {
                        color: '#409EFF'
                    },
                    name: '消息数'
                }]
            });
            
            // 监听窗口大小变化，重绘图表
            window.addEventListener('resize', () => {
                chart.resize();
            });
        },
        
        formatTime(timeStr) {
            const date = new Date(timeStr);
            return date.toLocaleString();
        },
        
        formatBytes(bytes, decimals = 2) {
            if (bytes === 0) return '0 Bytes';
            
            const k = 1024;
            const dm = decimals < 0 ? 0 : decimals;
            const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
            
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            
            return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
        }
    },
    template: `
        <div class="dashboard-container" v-loading="loading">
            <el-row :gutter="20">
                <!-- 系统状态卡片 -->
                <el-col :xs="24" :sm="12" :md="6">
                    <el-card class="status-card">
                        <div class="status-icon">
                            <i class="el-icon-monitor"></i>
                        </div>
                        <div class="status-info">
                            <div class="status-title">系统状态</div>
                            <div class="status-value" v-if="stats">
                                <el-progress 
                                    type="dashboard"
                                    :percentage="Math.round(stats.cpu.percent)" 
                                    :color="stats.cpu.percent > 80 ? '#F56C6C' : stats.cpu.percent > 60 ? '#E6A23C' : '#67C23A'">
                                    <template #default>
                                        <div class="progress-content">
                                            <span>CPU</span>
                                            <span class="progress-value">{{ Math.round(stats.cpu.percent) }}%</span>
                                        </div>
                                    </template>
                                </el-progress>
                            </div>
                        </div>
                    </el-card>
                </el-col>
                
                <!-- 内存使用卡片 -->
                <el-col :xs="24" :sm="12" :md="6">
                    <el-card class="status-card">
                        <div class="status-icon">
                            <i class="el-icon-coin"></i>
                        </div>
                        <div class="status-info">
                            <div class="status-title">内存使用</div>
                            <div class="status-value" v-if="stats">
                                <el-progress 
                                    type="dashboard"
                                    :percentage="Math.round(stats.memory.percent)" 
                                    :color="stats.memory.percent > 80 ? '#F56C6C' : stats.memory.percent > 60 ? '#E6A23C' : '#67C23A'">
                                    <template #default>
                                        <div class="progress-content">
                                            <span>MEM</span>
                                            <span class="progress-value">{{ Math.round(stats.memory.percent) }}%</span>
                                        </div>
                                    </template>
                                </el-progress>
                            </div>
                        </div>
                    </el-card>
                </el-col>
                
                <!-- 用户统计卡片 -->
                <el-col :xs="24" :sm="12" :md="6">
                    <el-card class="status-card">
                        <div class="status-icon">
                            <i class="el-icon-user"></i>
                        </div>
                        <div class="status-info">
                            <div class="status-title">用户总数</div>
                            <div class="status-value" v-if="botStats">
                                <span class="big-number">{{ botStats.user_count || 0 }}</span>
                            </div>
                        </div>
                    </el-card>
                </el-col>
                
                <!-- 群组统计卡片 -->
                <el-col :xs="24" :sm="12" :md="6">
                    <el-card class="status-card">
                        <div class="status-icon">
                            <i class="el-icon-chat-dot-round"></i>
                        </div>
                        <div class="status-info">
                            <div class="status-title">群组总数</div>
                            <div class="status-value" v-if="botStats">
                                <span class="big-number">{{ botStats.group_count || 0 }}</span>
                            </div>
                        </div>
                    </el-card>
                </el-col>
            </el-row>
            
            <el-row :gutter="20" style="margin-top: 20px;">
                <!-- 消息趋势图表 -->
                <el-col :xs="24" :md="16">
                    <el-card>
                        <template #header>
                            <div class="card-header">
                                <span>消息趋势</span>
                            </div>
                        </template>
                        <div id="message-trend-chart" style="height: 300px;"></div>
                    </el-card>
                </el-col>
                
                <!-- 最近消息列表 -->
                <el-col :xs="24" :md="8">
                    <el-card>
                        <template #header>
                            <div class="card-header">
                                <span>最近消息</span>
                            </div>
                        </template>
                        <div class="recent-messages">
                            <div v-for="(message, index) in recentMessages" :key="index" class="message-item">
                                <div class="message-sender">
                                    {{ message.sender.nickname }} 
                                    <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                                </div>
                                <div class="message-content">
                                    {{ message.content }}
                                </div>
                            </div>
                            
                            <div v-if="recentMessages.length === 0" class="no-messages">
                                暂无消息
                            </div>
                        </div>
                    </el-card>
                </el-col>
            </el-row>
            
            <el-row :gutter="20" style="margin-top: 20px;">
                <!-- 插件统计 -->
                <el-col :xs="24" :md="12">
                    <el-card>
                        <template #header>
                            <div class="card-header">
                                <span>插件统计</span>
                            </div>
                        </template>
                        <div class="plugin-stats" v-if="botStats">
                            <div class="stat-row">
                                <span>插件总数:</span>
                                <span>{{ botStats.plugin_count || 0 }}</span>
                            </div>
                            <div class="stat-row">
                                <span>已启用插件:</span>
                                <span>{{ botStats.enabled_plugin_count || 0 }}</span>
                            </div>
                            <div class="plugin-list" v-if="botStats.top_plugins">
                                <h4>最活跃插件</h4>
                                <div v-for="(plugin, index) in botStats.top_plugins" :key="index" class="plugin-item">
                                    <span>{{ plugin.name }}</span>
                                    <span>{{ plugin.call_count }} 次调用</span>
                                </div>
                            </div>
                        </div>
                    </el-card>
                </el-col>
                
                <!-- 系统信息 -->
                <el-col :xs="24" :md="12">
                    <el-card>
                        <template #header>
                            <div class="card-header">
                                <span>系统信息</span>
                            </div>
                        </template>
                        <div class="system-info" v-if="stats">
                            <div class="info-row">
                                <span>运行时间:</span>
                                <span>{{ stats.uptime.uptime_string }}</span>
                            </div>
                            <div class="info-row">
                                <span>操作系统:</span>
                                <span>{{ stats.system.os }}</span>
                            </div>
                            <div class="info-row">
                                <span>Python版本:</span>
                                <span>{{ stats.system.python }}</span>
                            </div>
                            <div class="info-row" v-if="stats.wechat.logged_in && stats.wechat.account_info">
                                <span>微信账号:</span>
                                <span>{{ stats.wechat.account_info.nickname }} ({{ stats.wechat.account_info.wxid }})</span>
                            </div>
                            <div class="info-row" v-if="stats.redis.connected">
                                <span>Redis状态:</span>
                                <span class="success-text">正常</span>
                            </div>
                            <div class="info-row" v-if="!stats.redis.connected">
                                <span>Redis状态:</span>
                                <span class="error-text">异常</span>
                            </div>
                        </div>
                    </el-card>
                </el-col>
            </el-row>
        </div>
    `
}; 