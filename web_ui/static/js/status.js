// 系统状态组件
const ComponentStatus = {
    data() {
        return {
            stats: null,
            loading: true,
            refreshInterval: null
        }
    },
    mounted() {
        this.fetchStatus();
        
        // 每30秒自动刷新一次
        this.refreshInterval = setInterval(() => {
            this.fetchStatus();
        }, 30000);
    },
    beforeUnmount() {
        // 清除定时器
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
    },
    methods: {
        fetchStatus() {
            this.loading = true;
            
            axios.get('/api/status')
                .then(response => {
                    this.stats = response.data.data;
                    this.loading = false;
                })
                .catch(error => {
                    console.error('获取系统状态失败:', error);
                    this.$message.error('获取系统状态失败');
                    this.loading = false;
                });
        },
        formatBytes(bytes, decimals = 2) {
            if (bytes === 0) return '0 Bytes';
            
            const k = 1024;
            const dm = decimals < 0 ? 0 : decimals;
            const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
            
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            
            return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
        },
        formatUptime(uptime) {
            if (!uptime) return '未知';
            
            const days = uptime.days;
            const hours = uptime.hours;
            const minutes = uptime.minutes;
            
            return `${days}天 ${hours}小时 ${minutes}分钟`;
        }
    },
    template: `
        <div v-loading="loading">
            <h2>系统状态</h2>
            
            <div v-if="stats" class="status-container">
                <el-card class="system-card">
                    <template #header>
                        <div class="card-header">
                            <span>系统信息</span>
                            <el-button size="small" @click="fetchStatus">刷新</el-button>
                        </div>
                    </template>
                    <div class="info-item">
                        <span class="label">操作系统:</span>
                        <span class="value">{{ stats.system.os }}</span>
                    </div>
                    <div class="info-item">
                        <span class="label">主机名:</span>
                        <span class="value">{{ stats.system.hostname }}</span>
                    </div>
                    <div class="info-item">
                        <span class="label">Python版本:</span>
                        <span class="value">{{ stats.system.python }}</span>
                    </div>
                    <div class="info-item">
                        <span class="label">运行时间:</span>
                        <span class="value">{{ stats.uptime.uptime_string }}</span>
                    </div>
                </el-card>
                
                <el-card class="resource-card">
                    <template #header>
                        <div class="card-header">
                            <span>资源使用</span>
                        </div>
                    </template>
                    <div class="resource-group">
                        <div class="resource-label">CPU使用率:</div>
                        <el-progress :percentage="stats.cpu.percent" :color="cpuColor"></el-progress>
                    </div>
                    <div class="resource-group">
                        <div class="resource-label">内存使用率:</div>
                        <el-progress :percentage="stats.memory.percent" :color="memoryColor"></el-progress>
                        <div class="resource-detail">
                            {{ formatBytes(stats.memory.used) }} / {{ formatBytes(stats.memory.total) }}
                        </div>
                    </div>
                    <div class="resource-group">
                        <div class="resource-label">磁盘使用率:</div>
                        <el-progress :percentage="stats.disk.percent" :color="diskColor"></el-progress>
                        <div class="resource-detail">
                            {{ formatBytes(stats.disk.used) }} / {{ formatBytes(stats.disk.total) }}
                        </div>
                    </div>
                </el-card>
                
                <el-card class="wechat-card">
                    <template #header>
                        <div class="card-header">
                            <span>微信状态</span>
                        </div>
                    </template>
                    <div v-if="stats.wechat.logged_in" class="wechat-info">
                        <div class="wechat-user">
                            <img :src="stats.wechat.account_info.avatar" class="wechat-avatar" v-if="stats.wechat.account_info.avatar">
                            <div class="wechat-avatar" v-else></div>
                            <div class="wechat-details">
                                <div class="wechat-nickname">{{ stats.wechat.account_info.nickname }}</div>
                                <div class="wechat-wxid">{{ stats.wechat.account_info.wxid }}</div>
                            </div>
                        </div>
                        <div class="wechat-status">
                            <el-tag type="success">已登录</el-tag>
                        </div>
                    </div>
                    <div v-else class="wechat-info">
                        <div class="wechat-status">
                            <el-tag type="danger">未登录</el-tag>
                        </div>
                        <div class="wechat-error" v-if="stats.wechat.error">
                            错误信息: {{ stats.wechat.error }}
                        </div>
                    </div>
                </el-card>
                
                <el-card class="redis-card">
                    <template #header>
                        <div class="card-header">
                            <span>Redis状态</span>
                        </div>
                    </template>
                    <div v-if="stats.redis.connected" class="redis-info">
                        <div class="info-item">
                            <span class="label">状态:</span>
                            <el-tag type="success">已连接</el-tag>
                        </div>
                        <div class="info-item">
                            <span class="label">内存使用:</span>
                            <span class="value">{{ stats.redis.memory_used }}</span>
                        </div>
                        <div class="info-item">
                            <span class="label">客户端连接:</span>
                            <span class="value">{{ stats.redis.clients_connected }}</span>
                        </div>
                    </div>
                    <div v-else class="redis-info">
                        <div class="info-item">
                            <span class="label">状态:</span>
                            <el-tag type="danger">未连接</el-tag>
                        </div>
                        <div class="redis-error" v-if="stats.redis.error">
                            错误信息: {{ stats.redis.error }}
                        </div>
                    </div>
                </el-card>
            </div>
        </div>
    `,
    computed: {
        cpuColor() {
            const percent = this.stats?.cpu?.percent || 0;
            return this.getColorByPercent(percent);
        },
        memoryColor() {
            const percent = this.stats?.memory?.percent || 0;
            return this.getColorByPercent(percent);
        },
        diskColor() {
            const percent = this.stats?.disk?.percent || 0;
            return this.getColorByPercent(percent);
        }
    },
    methods: {
        getColorByPercent(percent) {
            if (percent < 70) return '#67C23A';  // 绿色
            if (percent < 90) return '#E6A23C';  // 黄色
            return '#F56C6C';  // 红色
        }
    }
}; 