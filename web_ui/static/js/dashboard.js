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
            
            const messageChart = document.getElementById('message-chart');
            if (!messageChart) return;
            
            const chart = echarts.init(messageChart);
            
            const dates = this.botStats.daily_message_count.map(item => item.date);
            const counts = this.botStats.daily_message_count.map(item => item.count);
            
            const option = {
                title: {
                    text: '消息统计'
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
                    name: '消息数',
                    type: 'line',
                    data: counts,
                    areaStyle: {}
                }]
            };
            
            chart.setOption(option);
        },
        
        formatTime(time) {
            if (!time) return '';
            const date = new Date(time);
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
        <div v-loading="loading">
            <h2>系统概览</h2>
            
            <div class="dashboard-cards">
                <el-card class="stat-card">
                    <div class="stat-icon"><i class="el-icon-message"></i></div>
                    <div class="stat-content">
                        <div class="stat-title">今日消息</div>
                        <div class="stat-value">{{ botStats ? botStats.recent_message_count : 0 }}</div>
                    </div>
                </el-card>
                
                <el-card class="stat-card">
                    <div class="stat-icon"><i class="el-icon-user"></i></div>
                    <div class="stat-content">
                        <div class="stat-title">用户总数</div>
                        <div class="stat-value">{{ botStats ? botStats.user_count : 0 }}</div>
                    </div>
                </el-card>
                
                <el-card class="stat-card">
                    <div class="stat-icon"><i class="el-icon-s-cooperation"></i></div>
                    <div class="stat-content">
                        <div class="stat-title">群组总数</div>
                        <div class="stat-value">{{ botStats ? botStats.group_count : 0 }}</div>
                    </div>
                </el-card>
                
                <el-card class="stat-card">
                    <div class="stat-icon"><i class="el-icon-cpu"></i></div>
                    <div class="stat-content">
                        <div class="stat-title">插件数量</div>
                        <div class="stat-value">{{ botStats ? botStats.plugin_count : 0 }}</div>
                        <div class="stat-detail" v-if="botStats">已启用: {{ botStats.enabled_plugin_count }}</div>
                    </div>
                </el-card>
            </div>
            
            <div class="dashboard-charts">
                <el-card class="chart-card">
                    <div id="message-chart" style="width: 100%; height: 300px;"></div>
                </el-card>
            </div>
            
            <div class="dashboard-tables">
                <el-card class="table-card">
                    <template #header>
                        <div class="card-header">
                            <span>最近消息</span>
                        </div>
                    </template>
                    <el-table :data="recentMessages" style="width: 100%">
                        <el-table-column prop="sender_name" label="发送者" width="120"></el-table-column>
                        <el-table-column prop="content" label="内容"></el-table-column>
                        <el-table-column width="160">
                            <template #default="scope">
                                {{ formatTime(scope.row.timestamp) }}
                            </template>
                        </el-table-column>
                    </el-table>
                </el-card>
            </div>
        </div>
    `
}; 