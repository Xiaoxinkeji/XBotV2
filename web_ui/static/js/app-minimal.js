// 最简化版本Vue应用 - 用于测试
const { createApp } = Vue;
const { ElMessage } = ElementPlus;

// 创建应用
const app = createApp({
    data() {
        return {
            activeMenu: 'dashboard',
            isMobile: false,
            sidebarCollapsed: false,
            loading: false
        }
    },
    mounted() {
        console.log('Vue应用已挂载');
        this.checkDependencies();
    },
    methods: {
        toggleSidebar() {
            this.sidebarCollapsed = !this.sidebarCollapsed;
        },
        setActiveMenu(menu) {
            this.activeMenu = menu;
            console.log('切换到菜单:', menu);
        },
        checkDependencies() {
            // 检查必要的依赖是否加载
            console.log('Vue版本:', Vue.version);
            console.log('ElementPlus加载状态:', !!ElementPlus);
            console.log('Axios加载状态:', !!window.axios);
            console.log('ECharts加载状态:', !!window.echarts);
        }
    },
    template: `
    <div class="app-container" :class="{'is-mobile': isMobile}">
        <header class="app-header">
            <div class="header-left">
                <button @click="toggleSidebar" class="sidebar-toggle">
                    <span>菜单</span>
                </button>
                <h1 class="app-title">XYBot管理面板</h1>
            </div>
        </header>
        
        <aside class="app-sidebar" :class="{'collapsed': sidebarCollapsed}">
            <div class="sidebar-header">
                <img src="/static/img/logo.png" alt="Logo" class="sidebar-logo">
                <span class="sidebar-title">XYBot</span>
            </div>
            <nav class="sidebar-menu">
                <a @click="setActiveMenu('dashboard')" :class="{active: activeMenu === 'dashboard'}">控制面板</a>
                <a @click="setActiveMenu('plugins')" :class="{active: activeMenu === 'plugins'}">插件管理</a>
                <a @click="setActiveMenu('users')" :class="{active: activeMenu === 'users'}">用户管理</a>
                <a @click="setActiveMenu('messages')" :class="{active: activeMenu === 'messages'}">消息记录</a>
                <a @click="setActiveMenu('status')" :class="{active: activeMenu === 'status'}">系统状态</a>
            </nav>
        </aside>
        
        <main class="app-main">
            <div class="main-content">
                <h2>简化版本 - 测试页面</h2>
                <p>这是一个简化版本，用于测试基本的Vue和ElementPlus功能。</p>
                <el-button type="primary" @click="$message.success('ElementPlus按钮点击成功')">
                    测试ElementPlus
                </el-button>
            </div>
        </main>
    </div>
    `
});

// 使用ElementPlus
app.use(ElementPlus);

// 挂载应用
app.mount('#app');

console.log('最简化版本初始化完成'); 