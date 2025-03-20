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

// 主应用
const app = Vue.createApp({
    data() {
        return {
            activeMenu: localStorage.getItem('activeMenu') || 'dashboard',
            isMobile: window.innerWidth < 768,
            sidebarCollapsed: false
        }
    },
    mounted() {
        window.addEventListener('resize', this.handleResize);
        this.handleResize();
    },
    beforeUnmount() {
        window.removeEventListener('resize', this.handleResize);
    },
    methods: {
        handleResize() {
            this.isMobile = window.innerWidth < 768;
            if (this.isMobile) {
                this.sidebarCollapsed = true;
            }
        },
        toggleSidebar() {
            this.sidebarCollapsed = !this.sidebarCollapsed;
        },
        setActiveMenu(menu) {
            this.activeMenu = menu;
            localStorage.setItem('activeMenu', menu);
            if (this.isMobile) {
                this.sidebarCollapsed = true;
            }
        }
    },
    template: `
        <div class="app-container" :class="{'mobile': isMobile, 'sidebar-collapsed': sidebarCollapsed}">
            <!-- 侧边栏 -->
            <div class="sidebar">
                <div class="logo-container">
                    <img src="/static/img/logo.png" alt="XYBot Logo" class="logo" />
                    <span class="app-name" v-if="!sidebarCollapsed">XYBot管理</span>
                </div>
                
                <div class="menu-container">
                    <div class="menu-item" 
                        :class="{'active': activeMenu === 'dashboard'}" 
                        @click="setActiveMenu('dashboard')">
                        <i class="el-icon-monitor"></i>
                        <span v-if="!sidebarCollapsed">系统概览</span>
                    </div>
                    <div class="menu-item" 
                        :class="{'active': activeMenu === 'plugins'}" 
                        @click="setActiveMenu('plugins')">
                        <i class="el-icon-connection"></i>
                        <span v-if="!sidebarCollapsed">插件管理</span>
                    </div>
                    <div class="menu-item" 
                        :class="{'active': activeMenu === 'users'}" 
                        @click="setActiveMenu('users')">
                        <i class="el-icon-user"></i>
                        <span v-if="!sidebarCollapsed">用户与群组</span>
                    </div>
                    <div class="menu-item" 
                        :class="{'active': activeMenu === 'messages'}" 
                        @click="setActiveMenu('messages')">
                        <i class="el-icon-chat-line-square"></i>
                        <span v-if="!sidebarCollapsed">消息管理</span>
                    </div>
                    <div class="menu-item" 
                        :class="{'active': activeMenu === 'status'}" 
                        @click="setActiveMenu('status')">
                        <i class="el-icon-odometer"></i>
                        <span v-if="!sidebarCollapsed">系统状态</span>
                    </div>
                </div>
                
                <div class="sidebar-footer">
                    <div class="menu-item" @click="toggleSidebar">
                        <i :class="sidebarCollapsed ? 'el-icon-s-unfold' : 'el-icon-s-fold'"></i>
                        <span v-if="!sidebarCollapsed">收起菜单</span>
                    </div>
                </div>
            </div>
            
            <!-- 主内容区 -->
            <div class="main-content">
                <header class="app-header">
                    <div class="menu-toggle" @click="toggleSidebar" v-if="isMobile">
                        <i class="el-icon-menu"></i>
                    </div>
                    <h1 class="page-title">{{ {
                        'dashboard': '系统概览',
                        'plugins': '插件管理',
                        'users': '用户与群组',
                        'messages': '消息管理',
                        'status': '系统状态'
                    }[activeMenu] }}</h1>
                </header>
                
                <main class="content-area">
                    <component-dashboard v-if="activeMenu === 'dashboard'" />
                    <component-plugins v-if="activeMenu === 'plugins'" />
                    <component-users v-if="activeMenu === 'users'" />
                    <component-messages v-if="activeMenu === 'messages'" />
                    <component-status v-if="activeMenu === 'status'" />
                </main>
            </div>
        </div>
    `
});

// 注册组件
app.component('component-dashboard', ComponentDashboard);
console.log("仪表盘组件已注册");
app.component('component-plugins', ComponentPlugins);
console.log("插件组件已注册");
app.component('component-users', ComponentUsers);
console.log("用户组件已注册");
app.component('component-messages', ComponentMessages);
console.log("消息组件已注册");
app.component('component-status', ComponentStatus);
console.log("状态组件已注册");

// 挂载应用
app.use(ElementPlus);
app.provide('logOut', function() {
    axios.post('/api/auth/logout')
        .then(response => {
            window.location.href = '/login';
        })
        .catch(error => {
            console.error('登出失败:', error);
            this.$message.error('登出失败');
        });
});

// 改进API错误处理
axios.interceptors.response.use(
    response => {
        console.log(`API请求成功: ${response.config.url}`);
        return response;
    },
    error => {
        console.error(`API请求失败: ${error.config?.url}`, error);
        
        if (error.response) {
            // 如果是401错误，重定向到登录页
            if (error.response.status === 401) {
                console.log("用户未授权，重定向到登录页");
                window.location.href = '/login';
                return Promise.reject(error);
            }
            
            // 显示后端返回的错误信息
            const errorMsg = error.response.data?.message || '请求失败';
            ElementPlus.ElMessage.error(errorMsg);
        } else {
            // 网络错误等
            ElementPlus.ElMessage.error('网络连接失败，请检查网络设置');
        }
        return Promise.reject(error);
    }
);

// 在挂载前检查登录状态
const mountedApp = app.mount('#app');
console.log("Vue应用已挂载", mountedApp);

// 检查登录状态
axios.get('/api/auth/check')
    .catch(error => {
        if (error.response && error.response.status === 401) {
            window.location.href = '/login';
        }
    });

// 添加以下代码以优化移动端体验
if (window.innerWidth < 768) {
  // 为触摸设备优化侧边栏展开/收起
  const handleTouchStart = (e) => {
    app.touchStartX = e.touches[0].clientX;
  };
  
  const handleTouchEnd = (e) => {
    const touchEndX = e.changedTouches[0].clientX;
    const diff = touchEndX - app.touchStartX;
    
    // 从左向右滑动，显示侧边栏
    if (diff > 70 && app.touchStartX < 30) {
      app.sidebarCollapsed = false;
    }
    // 从右向左滑动，隐藏侧边栏
    else if (diff < -70 && !app.sidebarCollapsed) {
      app.sidebarCollapsed = true;
    }
  };
  
  // 添加触摸事件监听
  document.addEventListener('touchstart', handleTouchStart, { passive: true });
  document.addEventListener('touchend', handleTouchEnd, { passive: true });
  
  // 组件卸载时移除事件监听
  app.unmounted = () => {
    document.removeEventListener('touchstart', handleTouchStart);
    document.removeEventListener('touchend', handleTouchEnd);
  };
}

// 添加全局错误处理
app.config.errorHandler = (err, vm, info) => {
    console.error("Vue错误:", err);
    console.error("组件:", vm);
    console.error("信息:", info);
};

console.log("主JS文件已加载");

// 检查各组件是否正确定义
document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM已加载完成，检查组件状态");
    
    // 检查所有需要的组件
    const components = [
        { name: 'ComponentDashboard', obj: window.ComponentDashboard },
        { name: 'ComponentPlugins', obj: window.ComponentPlugins },
        { name: 'ComponentUsers', obj: window.ComponentUsers },
        { name: 'ComponentMessages', obj: window.ComponentMessages },
        { name: 'ComponentStatus', obj: window.ComponentStatus }
    ];
    
    let allComponentsLoaded = true;
    components.forEach(comp => {
        if (!comp.obj) {
            console.error(`${comp.name} 组件未定义或加载失败`);
            allComponentsLoaded = false;
        } else {
            console.log(`${comp.name} 组件已正确加载`);
        }
    });
    
    if (!allComponentsLoaded) {
        console.error("有组件未正确加载，页面可能无法正常显示");
    } else {
        console.log("所有组件加载成功");
    }
}); 