// 登录组件
const ComponentLogin = {
    data() {
        return {
            loginForm: {
                username: '',
                password: '',
                remember_me: false
            },
            loading: false,
            passwordVisible: false
        }
    },
    methods: {
        login() {
            if (!this.loginForm.username || !this.loginForm.password) {
                this.$message.warning('请输入用户名和密码');
                return;
            }
            
            this.loading = true;
            
            axios.post('/api/auth/login', this.loginForm)
                .then(response => {
                    this.$message.success('登录成功');
                    window.location.href = '/';
                })
                .catch(error => {
                    console.error('登录失败:', error);
                    this.$message.error(error.response?.data?.message || '登录失败');
                })
                .finally(() => {
                    this.loading = false;
                });
        }
    },
    template: `
        <div class="login-container">
            <div class="login-box">
                <div class="login-header">
                    <img src="/static/img/logo.png" alt="XYBot Logo" class="login-logo">
                    <h2>XYBot 管理系统</h2>
                </div>
                
                <el-form :model="loginForm" class="login-form">
                    <el-form-item>
                        <el-input 
                            v-model="loginForm.username" 
                            placeholder="用户名" 
                            prefix-icon="el-icon-user">
                        </el-input>
                    </el-form-item>
                    
                    <el-form-item>
                        <el-input 
                            v-model="loginForm.password" 
                            placeholder="密码" 
                            prefix-icon="el-icon-lock"
                            :type="passwordVisible ? 'text' : 'password'"
                            @keyup.enter="login">
                            <template #suffix>
                                <el-icon 
                                    class="password-icon" 
                                    @click="passwordVisible = !passwordVisible">
                                    <i :class="passwordVisible ? 'el-icon-view' : 'el-icon-hide'"></i>
                                </el-icon>
                            </template>
                        </el-input>
                    </el-form-item>
                    
                    <el-form-item>
                        <div class="remember-row">
                            <el-checkbox v-model="loginForm.remember_me">记住我</el-checkbox>
                        </div>
                    </el-form-item>
                    
                    <el-form-item>
                        <el-button 
                            type="primary" 
                            class="login-button" 
                            @click="login" 
                            :loading="loading">
                            登录
                        </el-button>
                    </el-form-item>
                </el-form>
                
                <div class="login-footer">
                    <p>XYBot © 2023 | 微信机器人管理系统</p>
                </div>
            </div>
        </div>
    `,
    mounted() {
        console.log("登录组件已挂载");
        
        // 捕获全局Vue错误
        this.$root.config.errorHandler = (err) => {
            console.error("Vue错误:", err);
        }
        
        // 检查Element Plus是否正确加载
        if (!window.ElementPlus) {
            console.error("Element Plus未正确加载!");
        }
    }
}; 