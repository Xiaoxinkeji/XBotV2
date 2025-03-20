// 组件定义
const ComponentDashboard = {
    template: `
        <div>
            <h2>控制面板</h2>
            <div class="card-container">
                <div class="stat-card">
                    <h3>机器人状态</h3>
                    <div class="stat-value">在线</div>
                    <p>运行时间: 3天12小时</p>
                </div>
                <div class="stat-card">
                    <h3>今日消息</h3>
                    <div class="stat-value">1,234</div>
                    <p>较昨日: <span style="color:green">+15%</span></p>
                </div>
                <div class="stat-card">
                    <h3>活跃用户</h3>
                    <div class="stat-value">89</div>
                    <p>本周: 246</p>
                </div>
                <div class="stat-card">
                    <h3>插件数量</h3>
                    <div class="stat-value">32</div>
                    <p>已启用: 28</p>
                </div>
            </div>
            <div id="chart-container" style="width:100%;height:300px;background:white;border-radius:4px;padding:20px;box-shadow:0 2px 12px 0 rgba(0,0,0,0.1)">
                <h3>消息统计</h3>
                <!-- 这里将放置图表 -->
            </div>
        </div>
    `
};

const ComponentPlugins = {
    data() {
        return {
            plugins: [],
            loading: true
        }
    },
    mounted() {
        this.fetchPlugins();
    },
    methods: {
        fetchPlugins() {
            this.loading = true;
            axios.get('/api/plugins')
                .then(response => {
                    this.plugins = response.data.data;
                    this.loading = false;
                })
                .catch(error => {
                    console.error('获取插件列表失败:', error);
                    this.loading = false;
                    this.$message.error('获取插件列表失败');
                });
        },
        togglePlugin(plugin) {
            axios.post(`/api/plugins/${plugin.name}/toggle`)
                .then(response => {
                    this.$message.success(`插件${plugin.name}状态切换中...`);
                    // 2秒后刷新列表以获取新状态
                    setTimeout(() => {
                        this.fetchPlugins();
                    }, 2000);
                })
                .catch(error => {
                    console.error('切换插件状态失败:', error);
                    this.$message.error('切换插件状态失败');
                });
        }
    },
    template: `
        <div>
            <h2>插件管理</h2>
            <el-button type="primary" @click="fetchPlugins">刷新</el-button>
            <el-table :data="plugins" style="width: 100%; margin-top: 20px" v-loading="loading">
                <el-table-column prop="name" label="插件名称" width="180" />
                <el-table-column prop="description" label="描述" />
                <el-table-column prop="author" label="作者" width="120" />
                <el-table-column prop="version" label="版本" width="100" />
                <el-table-column label="状态" width="100">
                    <template #default="scope">
                        <el-switch
                            v-model="scope.row.enabled"
                            @change="togglePlugin(scope.row)"
                        />
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="150">
                    <template #default="scope">
                        <el-button size="small" @click="$router.push('/plugins/'+scope.row.name)">详情</el-button>
                        <el-button size="small" type="primary">配置</el-button>
                    </template>
                </el-table-column>
            </el-table>
        </div>
    `
};

// 其他组件...

// Vue应用
const app = Vue.createApp({
    data() {
        return {
            current_page: 1
        }
    },
    mounted() {
        // 监听菜单点击
        document.querySelectorAll('.el-menu-item').forEach((item, index) => {
            item.addEventListener('click', () => {
                this.current_page = index + 1;
            });
        });
    }
});

// 注册组件
app.component('component-dashboard', ComponentDashboard);
app.component('component-plugins', ComponentPlugins);
// 注册其他组件...

// 挂载应用
app.mount('#app'); 