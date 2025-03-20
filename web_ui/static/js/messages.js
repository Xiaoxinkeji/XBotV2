// 消息管理组件
const ComponentMessages = {
    data() {
        return {
            activeTab: 'history',
            // 消息历史相关
            messages: [],
            loading: true,
            total: 0,
            offset: 0,
            limit: 20,
            filters: {
                sender: '',
                group: '',
                startTime: '',
                endTime: '',
                keyword: ''
            },
            
            // 统计相关
            stats: null,
            statsLoading: false,
            statsDays: 7,
            statsGroup: '',
            groups: []
        }
    },
    mounted() {
        this.fetchMessages();
        this.fetchGroups();
    },
    methods: {
        fetchMessages() {
            this.loading = true;
            
            // 构建查询参数
            const params = {
                limit: this.limit,
                offset: this.offset
            };
            
            if (this.filters.sender) params.sender = this.filters.sender;
            if (this.filters.group) params.group = this.filters.group;
            if (this.filters.startTime) params.start_time = this.filters.startTime;
            if (this.filters.endTime) params.end_time = this.filters.endTime;
            if (this.filters.keyword) params.keyword = this.filters.keyword;
            
            axios.get('/api/messages', { params })
                .then(response => {
                    this.messages = response.data.data;
                    this.total = response.data.pagination.total;
                    this.loading = false;
                })
                .catch(error => {
                    console.error('获取消息历史失败:', error);
                    this.$message.error('获取消息历史失败');
                    this.loading = false;
                });
        },
        
        pageChange(page) {
            this.offset = (page - 1) * this.limit;
            this.fetchMessages();
        },
        
        searchMessages() {
            this.offset = 0;
            this.fetchMessages();
        },
        
        clearFilters() {
            this.filters = {
                sender: '',
                group: '',
                startTime: '',
                endTime: '',
                keyword: ''
            };
            this.offset = 0;
            this.fetchMessages();
        },
        
        fetchGroups() {
            axios.get('/api/users/groups?limit=100')
                .then(response => {
                    this.groups = response.data.data;
                })
                .catch(error => {
                    console.error('获取群组列表失败:', error);
                });
        },
        
        fetchStats() {
            if (this.activeTab !== 'stats') return;
            
            this.statsLoading = true;
            const params = { days: this.statsDays };
            if (this.statsGroup) params.group_wxid = this.statsGroup;
            
            axios.get('/api/messages/stats', { params })
                .then(response => {
                    this.stats = response.data.data;
                    this.statsLoading = false;
                    
                    // 渲染图表
                    this.$nextTick(() => {
                        this.renderDailyChart();
                        this.renderGroupsChart();
                        this.renderUsersChart();
                    });
                })
                .catch(error => {
                    console.error('获取消息统计失败:', error);
                    this.$message.error('获取消息统计失败');
                    this.statsLoading = false;
                });
        },
        
        renderDailyChart() {
            if (!this.stats || !this.stats.daily_stats) return;
            
            const dailyChart = echarts.init(document.getElementById('daily-chart'));
            const dates = this.stats.daily_stats.map(item => item.date);
            const counts = this.stats.daily_stats.map(item => item.count);
            
            dailyChart.setOption({
                title: {
                    text: '每日消息统计'
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
            });
        },
        
        renderGroupsChart() {
            if (!this.stats || !this.stats.top_groups) return;
            
            const groupsChart = echarts.init(document.getElementById('groups-chart'));
            const groups = this.stats.top_groups.map(item => item.name);
            const counts = this.stats.top_groups.map(item => item.message_count);
            
            groupsChart.setOption({
                title: {
                    text: '最活跃群组'
                },
                tooltip: {
                    trigger: 'axis'
                },
                xAxis: {
                    type: 'category',
                    data: groups
                },
                yAxis: {
                    type: 'value'
                },
                series: [{
                    name: '消息数',
                    type: 'bar',
                    data: counts
                }]
            });
        },
        
        renderUsersChart() {
            if (!this.stats || !this.stats.top_users) return;
            
            const usersChart = echarts.init(document.getElementById('users-chart'));
            const users = this.stats.top_users.map(item => item.nickname);
            const userCounts = this.stats.top_users.map(item => item.message_count);
            
            usersChart.setOption({
                title: {
                    text: '最活跃用户'
                },
                tooltip: {
                    trigger: 'axis'
                },
                xAxis: {
                    type: 'category',
                    data: users
                },
                yAxis: {
                    type: 'value'
                },
                series: [{
                    name: '消息数',
                    type: 'bar',
                    data: userCounts
                }]
            });
        },
        
        handleTabChange(tab) {
            if (tab.name === 'stats') {
                this.fetchStats();
            }
        },
        
        refreshStats() {
            this.fetchStats();
        },
        
        formatTime(timeStr) {
            const date = new Date(timeStr);
            return date.toLocaleString();
        },
        
        formatMessageContent(message) {
            if (!message.content) return '';
            
            // 处理特殊类型消息
            if (message.content.startsWith('[图片]') || message.content.startsWith('[Image]')) {
                return '【图片消息】';
            } else if (message.content.startsWith('[视频]') || message.content.startsWith('[Video]')) {
                return '【视频消息】';
            } else if (message.content.startsWith('[语音]') || message.content.startsWith('[Voice]')) {
                return '【语音消息】';
            } else if (message.content.startsWith('[文件]') || message.content.startsWith('[File]')) {
                return '【文件消息】';
            } else if (message.content.startsWith('[表情]') || message.content.startsWith('[Emoji]')) {
                return '【表情消息】';
            } else if (message.content.startsWith('[位置]') || message.content.startsWith('[Location]')) {
                return '【位置消息】';
            } else if (message.content.startsWith('[链接]') || message.content.startsWith('[Link]')) {
                return '【链接消息】';
            } else {
                return message.content;
            }
        }
    },
    template: `
        <div>
            <h2>消息管理</h2>
            
            <el-tabs v-model="activeTab" @tab-click="handleTabChange">
                <el-tab-pane label="消息历史" name="history">
                    <div class="filter-bar">
                        <el-form :inline="true" class="message-filter-form">
                            <el-form-item label="发送者">
                                <el-input v-model="filters.sender" placeholder="发送者ID"></el-input>
                            </el-form-item>
                            <el-form-item label="群组">
                                <el-select v-model="filters.group" placeholder="选择群组" clearable>
                                    <el-option
                                        v-for="group in groups"
                                        :key="group.wxid"
                                        :label="group.name"
                                        :value="group.wxid">
                                    </el-option>
                                </el-select>
                            </el-form-item>
                            <el-form-item label="开始时间">
                                <el-date-picker
                                    v-model="filters.startTime"
                                    type="datetime"
                                    placeholder="选择开始时间"
                                    format="YYYY-MM-DD HH:mm:ss"
                                    value-format="YYYY-MM-DDTHH:mm:ss">
                                </el-date-picker>
                            </el-form-item>
                            <el-form-item label="结束时间">
                                <el-date-picker
                                    v-model="filters.endTime"
                                    type="datetime"
                                    placeholder="选择结束时间"
                                    format="YYYY-MM-DD HH:mm:ss"
                                    value-format="YYYY-MM-DDTHH:mm:ss">
                                </el-date-picker>
                            </el-form-item>
                            <el-form-item label="关键词">
                                <el-input v-model="filters.keyword" placeholder="搜索关键词"></el-input>
                            </el-form-item>
                            <el-form-item>
                                <el-button type="primary" @click="searchMessages">搜索</el-button>
                                <el-button @click="clearFilters">清空</el-button>
                            </el-form-item>
                        </el-form>
                    </div>
                    
                    <el-table :data="messages" style="width: 100%" v-loading="loading">
                        <el-table-column prop="timestamp" label="时间" width="180">
                            <template #default="scope">
                                {{ formatTime(scope.row.timestamp) }}
                            </template>
                        </el-table-column>
                        <el-table-column label="发送者" width="150">
                            <template #default="scope">
                                {{ scope.row.sender.nickname }} ({{ scope.row.sender.wxid }})
                            </template>
                        </el-table-column>
                        <el-table-column label="接收方" width="150">
                            <template #default="scope">
                                <span v-if="scope.row.type === 'group'">
                                    {{ scope.row.group.name }} ({{ scope.row.group.wxid }})
                                </span>
                                <span v-else>
                                    {{ scope.row.receiver.nickname }} ({{ scope.row.receiver.wxid }})
                                </span>
                            </template>
                        </el-table-column>
                        <el-table-column label="内容">
                            <template #default="scope">
                                {{ formatMessageContent(scope.row) }}
                            </template>
                        </el-table-column>
                    </el-table>
                    
                    <el-pagination
                        @current-change="pageChange"
                        :current-page="offset / limit + 1"
                        :page-size="limit"
                        :total="total"
                        layout="total, prev, pager, next"
                        style="margin-top: 20px;">
                    </el-pagination>
                </el-tab-pane>
                
                <el-tab-pane label="消息统计" name="stats">
                    <div class="stats-filter-bar">
                        <el-form :inline="true">
                            <el-form-item label="统计天数">
                                <el-select v-model="statsDays">
                                    <el-option :value="7" label="最近7天"></el-option>
                                    <el-option :value="14" label="最近14天"></el-option>
                                    <el-option :value="30" label="最近30天"></el-option>
                                </el-select>
                            </el-form-item>
                            <el-form-item label="群组">
                                <el-select v-model="statsGroup" placeholder="所有群组" clearable>
                                    <el-option
                                        v-for="group in groups"
                                        :key="group.wxid"
                                        :label="group.name"
                                        :value="group.wxid">
                                    </el-option>
                                </el-select>
                            </el-form-item>
                            <el-form-item>
                                <el-button type="primary" @click="refreshStats">刷新统计</el-button>
                            </el-form-item>
                        </el-form>
                    </div>
                    
                    <div class="stats-overview" v-if="stats" v-loading="statsLoading">
                        <el-card class="total-card">
                            <div class="total-messages">
                                <h3>总消息数</h3>
                                <div class="total-value">{{ stats.total_messages }}</div>
                            </div>
                        </el-card>
                        
                        <div class="charts-container">
                            <div id="daily-chart" class="chart-item"></div>
                            <div id="groups-chart" class="chart-item"></div>
                            <div id="users-chart" class="chart-item"></div>
                        </div>
                    </div>
                </el-tab-pane>
            </el-tabs>
        </div>
    `
}; 