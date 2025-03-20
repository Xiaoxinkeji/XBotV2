// 系统状态组件
const ComponentStatus = {
    data() {
        return {
            status: null,
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
                    this.status = response.data.data;
                    this.loading = false;
                })
                .catch(error => {
                    console.error('获取系统状态失败:', error);
                    this.$message.error('获取系统状态失败');
                    this.loading = false;
                });
        },
        refreshStatus() {
            this.fetchStatus();
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
        <div>
            <h2>系统状态</h2>
            
            <div class="action-bar">
                <el-button type="primary" @click="refreshStatus" :loading="loading">刷新</el-button>
            </div>
            
            <div class="status-container" v-loading="loading" v-if="status">
                <el-row :gutter="20">
                    <el-col :span="12">
                        <el-card class="status-card">
                            <template #header>
                                <div class="card-header">
                                    <span>系统信息</span>
                                </div>
                            </template>
                            <div class="system-info">
                                <p><strong>操作系统:</strong> {{ status.system.os }}</p>
                                <p><strong>Python版本:</strong> {{ status.system.python }}</p>
                                <p><strong>主机名:</strong> {{ status.system.hostname }}</p>
                                <p><strong>启动时间:</strong> {{ status.uptime.start_time }}</p>
                                <p><strong>运行时长:</strong> {{ status.uptime.uptime_string }}</p>
                            </div>
                        </el-card>
                    </el-col>
                    
                    <el-col :span="12">
                        <el-card class="status-card">
                            <template #header>
                                <div class="card-header">
                                    <span>资源使用</span>
                                </div>
                            </template>
                            <div class="resource-usage">
                                <div class="resource-item">
                                    <span>CPU使用率</span>
                                    <el-progress 
                                        :percentage="status.cpu.percent"
                                        :color="status.cpu.percent > 80 ? '#F56C6C' : status.cpu.percent > 60 ? '#E6A23C' : '#67C23A'">
                                    </el-progress>
                                </div>
                                <div class="resource-item">
                                    <span>内存使用率</span>
                                    <el-progress 
                                        :percentage="status.memory.percent"
                                        :color="status.memory.percent > 80 ? '#F56C6C' : status.memory.percent > 60 ? '#E6A23C' : '#67C23A'">
                                    </el-progress>
                                    <div class="memory-details">
                                        <small>已用: {{ formatBytes(status.memory.used) }} / 总计: {{ formatBytes(status.memory.total) }}</small>
                                    </div>
                                </div>
                                <div class="resource-item">
                                    <span>磁盘使用率</span>
                                    <el-progress 
                                        :percentage="status.disk.percent"
                                        :color="status.disk.percent > 80 ? '#F56C6C' : status.disk.percent > 60 ? '#E6A23C' : '#67C23A'">
                                    </el-progress>
                                    <div class="disk-details">
                                        <small>已用: {{ formatBytes(status.disk.used) }} / 总计: {{ formatBytes(status.disk.total) }}</small>
                                    </div>
                                </div>
                            </div>
                        </el-card>
                    </el-col>
                </el-row>
                
                <el-row :gutter="20" style="margin-top: 20px;">
                    <el-col :span="12">
                        <el-card class="status-card">
                            <template #header>
                                <div class="card-header">
                                    <span>微信账号状态</span>
                                </div>
                            </template>
                            <div class="wechat-status">
                                <div v-if="status.wechat.logged_in">
                                    <p><i class="el-icon-success" style="color: #67C23A;"></i> 已登录</p>
                                    <p v-if="status.wechat.account_info">
                                        <strong>微信ID:</strong> {{ status.wechat.account_info.wxid }}<br>
                                        <strong>昵称:</strong> {{ status.wechat.account_info.nickname }}
                                    </p>
                                </div>
                                <div v-else>
                                    <p><i class="el-icon-error" style="color: #F56C6C;"></i> 未登录</p>
                                    <p v-if="status.wechat.error">
                                        <strong>错误信息:</strong> {{ status.wechat.error }}
                                    </p>
                                </div>
                            </div>
                        </el-card>
                    </el-col>
                    
                    <el-col :span="12">
                        <el-card class="status-card">
                            <template #header>
                                <div class="card-header">
                                    <span>Redis状态</span>
                                </div>
                            </template>
                            <div class="redis-status">
                                <div v-if="status.redis.connected">
                                    <p><i class="el-icon-success" style="color: #67C23A;"></i> 已连接</p>
                                    <p>
                                        <strong>内存使用:</strong> {{ status.redis.memory_used }}<br>
                                        <strong>客户端连接数:</strong> {{ status.redis.clients_connected }}
                                    </p>
                                </div>
                                <div v-else>
                                    <p><i class="el-icon-error" style="color: #F56C6C;"></i> 连接失败</p>
                                    <p v-if="status.redis.error">
                                        <strong>错误信息:</strong> {{ status.redis.error }}
                                    </p>
                                </div>
                            </div>
                        </el-card>
                    </el-col>
                </el-row>
            </div>
        </div>
    `
}; 