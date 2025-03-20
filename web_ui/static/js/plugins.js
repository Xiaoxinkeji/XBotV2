// 插件管理组件
const ComponentPlugins = {
    data() {
        return {
            plugins: [],
            loading: true,
            categories: {},
            activeTab: 'all',
            pluginDetailVisible: false,
            currentPlugin: null,
            configValue: '',
            configLoading: false,
            uploadDialogVisible: false,
            uploadFile: null,
            uploadLoading: false
        }
    },
    mounted() {
        this.fetchPlugins();
        this.fetchCategories();
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
        fetchCategories() {
            axios.get('/api/plugins/categories')
                .then(response => {
                    this.categories = response.data.data;
                })
                .catch(error => {
                    console.error('获取插件分类失败:', error);
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
        },
        showPluginDetail(plugin) {
            this.currentPlugin = plugin;
            this.configLoading = true;
            this.pluginDetailVisible = true;
            
            axios.get(`/api/plugins/${plugin.name}`)
                .then(response => {
                    this.configValue = JSON.stringify(response.data.data.config, null, 2);
                    this.configLoading = false;
                })
                .catch(error => {
                    console.error('获取插件详情失败:', error);
                    this.$message.error('获取插件详情失败');
                    this.configLoading = false;
                });
        },
        savePluginConfig() {
            try {
                const config = JSON.parse(this.configValue);
                this.configLoading = true;
                
                axios.post(`/api/plugins/${this.currentPlugin.name}/config`, config)
                    .then(response => {
                        this.$message.success('配置保存成功，插件可能需要重启才能生效');
                        this.configLoading = false;
                        this.pluginDetailVisible = false;
                    })
                    .catch(error => {
                        console.error('保存配置失败:', error);
                        this.$message.error('保存配置失败: ' + error.response?.data?.detail || error.message);
                        this.configLoading = false;
                    });
            } catch (e) {
                this.$message.error('配置格式错误: ' + e.message);
            }
        },
        handleFileChange(file) {
            this.uploadFile = file;
        },
        uploadPlugin() {
            if (!this.uploadFile) {
                this.$message.warning('请选择插件文件');
                return;
            }
            
            const formData = new FormData();
            formData.append('plugin_file', this.uploadFile.raw);
            this.uploadLoading = true;
            
            axios.post('/api/plugins/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            })
            .then(response => {
                this.$message.success(`插件上传成功: ${response.data.data.plugin_name}`);
                this.uploadLoading = false;
                this.uploadDialogVisible = false;
                this.fetchPlugins();
            })
            .catch(error => {
                console.error('上传插件失败:', error);
                this.$message.error('上传插件失败: ' + error.response?.data?.detail || error.message);
                this.uploadLoading = false;
            });
        },
        filteredPlugins() {
            if (this.activeTab === 'all') {
                return this.plugins;
            } else {
                return this.plugins.filter(p => {
                    return p.category === this.activeTab;
                });
            }
        }
    },
    template: `
        <div>
            <h2>插件管理</h2>
            <div class="action-bar">
                <el-button type="primary" @click="fetchPlugins">刷新</el-button>
                <el-button type="success" @click="uploadDialogVisible = true">
                    <i class="el-icon-upload"></i> 上传插件
                </el-button>
            </div>
            
            <el-tabs v-model="activeTab" class="plugin-tabs">
                <el-tab-pane label="全部插件" name="all"></el-tab-pane>
                <el-tab-pane 
                    v-for="(plugins, category) in categories" 
                    :key="category"
                    :label="category" 
                    :name="category">
                </el-tab-pane>
            </el-tabs>
            
            <el-table :data="filteredPlugins()" style="width: 100%; margin-top: 20px" v-loading="loading">
                <el-table-column prop="name" label="插件名称" width="180" />
                <el-table-column prop="description" label="描述" />
                <el-table-column prop="author" label="作者" width="120" />
                <el-table-column prop="version" label="版本" width="100" />
                <el-table-column prop="category" label="分类" width="100" />
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
                        <el-button size="small" @click="showPluginDetail(scope.row)">详情</el-button>
                    </template>
                </el-table-column>
            </el-table>
            
            <!-- 插件详情对话框 -->
            <el-dialog
                title="插件详情"
                v-model="pluginDetailVisible"
                width="70%">
                <div v-if="currentPlugin" class="plugin-detail">
                    <h3>{{ currentPlugin.name }} <small>v{{ currentPlugin.version }}</small></h3>
                    <p><strong>作者:</strong> {{ currentPlugin.author }}</p>
                    <p><strong>描述:</strong> {{ currentPlugin.description }}</p>
                    <p><strong>分类:</strong> {{ currentPlugin.category || '未分类' }}</p>
                    
                    <div class="config-editor">
                        <h4>配置文件</h4>
                        <el-input
                            type="textarea"
                            v-model="configValue"
                            :rows="15"
                            placeholder="暂无配置信息"
                            v-loading="configLoading">
                        </el-input>
                    </div>
                </div>
                <template #footer>
                    <span class="dialog-footer">
                        <el-button @click="pluginDetailVisible = false">取消</el-button>
                        <el-button type="primary" @click="savePluginConfig">保存配置</el-button>
                    </span>
                </template>
            </el-dialog>
            
            <!-- 上传插件对话框 -->
            <el-dialog
                title="上传插件"
                v-model="uploadDialogVisible"
                width="500px">
                <el-upload
                    class="upload-demo"
                    drag
                    action="#"
                    :auto-upload="false"
                    :on-change="handleFileChange"
                    :limit="1">
                    <i class="el-icon-upload"></i>
                    <div class="el-upload__text">将插件包拖到此处，或<em>点击上传</em></div>
                    <div class="el-upload__tip">请上传zip格式的插件包，插件包内应包含插件目录</div>
                </el-upload>
                <template #footer>
                    <span class="dialog-footer">
                        <el-button @click="uploadDialogVisible = false">取消</el-button>
                        <el-button type="primary" @click="uploadPlugin" :loading="uploadLoading">上传</el-button>
                    </span>
                </template>
            </el-dialog>
        </div>
    `
}; 