// 用户和群组管理组件
const ComponentUsers = {
    data() {
        return {
            activeTab: 'users',
            // 用户相关数据
            users: [],
            userLoading: true,
            userTotal: 0,
            userOffset: 0,
            userLimit: 20,
            userKeyword: '',
            userDetailVisible: false,
            currentUser: null,
            
            // 群组相关数据
            groups: [],
            groupLoading: true,
            groupTotal: 0,
            groupOffset: 0,
            groupLimit: 20,
            groupKeyword: '',
            groupDetailVisible: false,
            currentGroup: null,
            groupMembers: [],
            
            // 白名单相关数据
            whitelist: [],
            whitelistLoading: false,
            whitelistDialogVisible: false,
            whitelistForm: {
                wxid: ''
            },
            
            // 积分编辑相关
            pointsDialogVisible: false,
            pointsForm: {
                wxid: '',
                nickname: '',
                currentPoints: 0,
                newPoints: 0
            }
        }
    },
    mounted() {
        this.fetchUsers();
        if (this.activeTab === 'whitelist') {
            this.fetchWhitelist();
        }
    },
    methods: {
        // 用户相关方法
        fetchUsers() {
            this.userLoading = true;
            axios.get(`/api/users?limit=${this.userLimit}&offset=${this.userOffset}&keyword=${this.userKeyword}`)
                .then(response => {
                    this.users = response.data.data;
                    this.userTotal = response.data.pagination.total;
                    this.userLoading = false;
                })
                .catch(error => {
                    console.error('获取用户列表失败:', error);
                    this.$message.error('获取用户列表失败');
                    this.userLoading = false;
                });
        },
        userPageChange(page) {
            this.userOffset = (page - 1) * this.userLimit;
            this.fetchUsers();
        },
        searchUsers() {
            this.userOffset = 0;
            this.fetchUsers();
        },
        
        // 群组相关方法
        fetchGroups() {
            if (this.activeTab !== 'groups') return;
            
            this.groupLoading = true;
            axios.get(`/api/users/groups?limit=${this.groupLimit}&offset=${this.groupOffset}&keyword=${this.groupKeyword}`)
                .then(response => {
                    this.groups = response.data.data;
                    this.groupTotal = response.data.pagination.total;
                    this.groupLoading = false;
                })
                .catch(error => {
                    console.error('获取群组列表失败:', error);
                    this.$message.error('获取群组列表失败');
                    this.groupLoading = false;
                });
        },
        groupPageChange(page) {
            this.groupOffset = (page - 1) * this.groupLimit;
            this.fetchGroups();
        },
        searchGroups() {
            this.groupOffset = 0;
            this.fetchGroups();
        },
        showGroupDetail(group) {
            this.currentGroup = group;
            this.groupDetailVisible = true;
            this.fetchGroupMembers(group.wxid);
        },
        fetchGroupMembers(groupWxid) {
            axios.get(`/api/users/groups/${groupWxid}/members`)
                .then(response => {
                    this.groupMembers = response.data.data.members;
                })
                .catch(error => {
                    console.error('获取群成员失败:', error);
                    this.$message.error('获取群成员失败');
                });
        },
        
        // 白名单相关方法
        fetchWhitelist() {
            this.whitelistLoading = true;
            axios.get('/api/users/whitelist')
                .then(response => {
                    this.whitelist = response.data.data;
                    this.whitelistLoading = false;
                })
                .catch(error => {
                    console.error('获取白名单失败:', error);
                    this.$message.error('获取白名单失败');
                    this.whitelistLoading = false;
                });
        },
        addToWhitelist() {
            if (!this.whitelistForm.wxid) {
                this.$message.warning('请输入微信ID');
                return;
            }
            
            const newWhitelist = [...this.whitelist, this.whitelistForm.wxid];
            axios.post('/api/users/whitelist', newWhitelist)
                .then(response => {
                    this.$message.success('添加白名单成功');
                    this.whitelistDialogVisible = false;
                    this.whitelistForm.wxid = '';
                    this.fetchWhitelist();
                })
                .catch(error => {
                    console.error('添加白名单失败:', error);
                    this.$message.error('添加白名单失败');
                });
        },
        removeFromWhitelist(wxid) {
            this.$confirm(`确定从白名单中移除 ${wxid} 吗?`, '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(() => {
                const newWhitelist = this.whitelist.filter(id => id !== wxid);
                axios.post('/api/users/whitelist', newWhitelist)
                    .then(response => {
                        this.$message.success('移除白名单成功');
                        this.fetchWhitelist();
                    })
                    .catch(error => {
                        console.error('移除白名单失败:', error);
                        this.$message.error('移除白名单失败');
                    });
            }).catch(() => {
                // 取消操作
            });
        },
        
        // 积分管理相关方法
        showPointsDialog(user) {
            this.pointsForm = {
                wxid: user.wxid,
                nickname: user.nickname,
                currentPoints: user.points,
                newPoints: user.points
            };
            this.pointsDialogVisible = true;
        },
        updatePoints() {
            if (this.pointsForm.newPoints === this.pointsForm.currentPoints) {
                this.pointsDialogVisible = false;
                return;
            }
            
            axios.post('/api/users/update-points', {
                wxid: this.pointsForm.wxid,
                points: this.pointsForm.newPoints
            })
                .then(response => {
                    this.$message.success('积分更新成功');
                    this.pointsDialogVisible = false;
                    this.fetchUsers(); // 刷新用户列表
                })
                .catch(error => {
                    console.error('更新积分失败:', error);
                    this.$message.error('更新积分失败');
                });
        },
        
        // Tab切换处理
        handleTabChange(tab) {
            if (tab.name === 'groups') {
                this.fetchGroups();
            } else if (tab.name === 'whitelist') {
                this.fetchWhitelist();
            }
        }
    },
    template: `
        <div>
            <h2>用户与群组管理</h2>
            
            <el-tabs v-model="activeTab" @tab-click="handleTabChange">
                <el-tab-pane label="用户管理" name="users">
                    <div class="search-bar">
                        <el-input
                            v-model="userKeyword"
                            placeholder="输入用户昵称或ID搜索"
                            prefix-icon="el-icon-search"
                            @keyup.enter="searchUsers"
                            clearable
                            style="width: 300px;">
                        </el-input>
                        <el-button type="primary" @click="searchUsers">搜索</el-button>
                    </div>
                    
                    <el-table :data="users" style="width: 100%; margin-top: 20px" v-loading="userLoading">
                        <el-table-column prop="wxid" label="用户ID" width="180" />
                        <el-table-column prop="nickname" label="昵称" />
                        <el-table-column prop="points" label="积分" width="100" sortable />
                        <el-table-column prop="sign_in_count" label="签到次数" width="100" sortable />
                        <el-table-column prop="last_sign_in" label="最后签到" width="180" sortable />
                        <el-table-column label="操作" width="150">
                            <template #default="scope">
                                <el-button size="small" @click="showPointsDialog(scope.row)">修改积分</el-button>
                            </template>
                        </el-table-column>
                    </el-table>
                    
                    <el-pagination
                        @current-change="userPageChange"
                        :current-page="userOffset / userLimit + 1"
                        :page-size="userLimit"
                        :total="userTotal"
                        layout="total, prev, pager, next"
                        style="margin-top: 20px;">
                    </el-pagination>
                </el-tab-pane>
                
                <el-tab-pane label="群组管理" name="groups">
                    <div class="search-bar">
                        <el-input
                            v-model="groupKeyword"
                            placeholder="输入群名称或ID搜索"
                            prefix-icon="el-icon-search"
                            @keyup.enter="searchGroups"
                            clearable
                            style="width: 300px;">
                        </el-input>
                        <el-button type="primary" @click="searchGroups">搜索</el-button>
                    </div>
                    
                    <el-table :data="groups" style="width: 100%; margin-top: 20px" v-loading="groupLoading">
                        <el-table-column prop="wxid" label="群ID" width="180" />
                        <el-table-column prop="name" label="群名称" />
                        <el-table-column prop="member_count" label="成员数" width="100" />
                        <el-table-column prop="owner_wxid" label="群主ID" width="180" />
                        <el-table-column label="操作" width="150">
                            <template #default="scope">
                                <el-button size="small" @click="showGroupDetail(scope.row)">查看成员</el-button>
                            </template>
                        </el-table-column>
                    </el-table>
                    
                    <el-pagination
                        @current-change="groupPageChange"
                        :current-page="groupOffset / groupLimit + 1"
                        :page-size="groupLimit"
                        :total="groupTotal"
                        layout="total, prev, pager, next"
                        style="margin-top: 20px;">
                    </el-pagination>
                </el-tab-pane>
                
                <el-tab-pane label="白名单管理" name="whitelist">
                    <div class="action-bar">
                        <el-button type="primary" @click="whitelistDialogVisible = true">添加白名单</el-button>
                        <el-button type="success" @click="fetchWhitelist">刷新</el-button>
                    </div>
                    
                    <el-table :data="whitelist" style="width: 100%; margin-top: 20px" v-loading="whitelistLoading">
                        <el-table-column prop="" label="序号" width="80">
                            <template #default="scope">
                                {{ scope.$index + 1 }}
                            </template>
                        </el-table-column>
                        <el-table-column prop="" label="微信ID">
                            <template #default="scope">
                                {{ scope.row }}
                            </template>
                        </el-table-column>
                        <el-table-column label="操作" width="150">
                            <template #default="scope">
                                <el-button size="small" type="danger" @click="removeFromWhitelist(scope.row)">移除</el-button>
                            </template>
                        </el-table-column>
                    </el-table>
                </el-tab-pane>
            </el-tabs>
            
            <!-- 群组详情对话框 -->
            <el-dialog
                title="群成员列表"
                v-model="groupDetailVisible"
                width="80%">
                <div v-if="currentGroup" class="group-detail">
                    <h3>{{ currentGroup.name }}</h3>
                    <p>群ID: {{ currentGroup.wxid }}</p>
                    <p>成员数: {{ currentGroup.member_count }}</p>
                    
                    <el-table :data="groupMembers" style="width: 100%; margin-top: 20px">
                        <el-table-column prop="wxid" label="用户ID" width="180" />
                        <el-table-column prop="nickname" label="昵称" />
                        <el-table-column prop="group_nickname" label="群昵称" />
                        <el-table-column label="管理员" width="100">
                            <template #default="scope">
                                <el-tag v-if="scope.row.is_admin" type="success">是</el-tag>
                                <el-tag v-else type="info">否</el-tag>
                            </template>
                        </el-table-column>
                        <el-table-column prop="join_time" label="加入时间" width="180" />
                    </el-table>
                </div>
            </el-dialog>
            
            <!-- 白名单添加对话框 -->
            <el-dialog
                title="添加白名单"
                v-model="whitelistDialogVisible"
                width="500px">
                <el-form :model="whitelistForm" label-width="80px">
                    <el-form-item label="微信ID">
                        <el-input v-model="whitelistForm.wxid" placeholder="请输入微信ID"></el-input>
                    </el-form-item>
                </el-form>
                <template #footer>
                    <span class="dialog-footer">
                        <el-button @click="whitelistDialogVisible = false">取消</el-button>
                        <el-button type="primary" @click="addToWhitelist">添加</el-button>
                    </span>
                </template>
            </el-dialog>
            
            <!-- 积分编辑对话框 -->
            <el-dialog
                title="修改用户积分"
                v-model="pointsDialogVisible"
                width="500px">
                <el-form :model="pointsForm" label-width="120px">
                    <el-form-item label="用户ID">
                        <el-input v-model="pointsForm.wxid" disabled></el-input>
                    </el-form-item>
                    <el-form-item label="用户昵称">
                        <el-input v-model="pointsForm.nickname" disabled></el-input>
                    </el-form-item>
                    <el-form-item label="当前积分">
                        <el-input v-model="pointsForm.currentPoints" disabled></el-input>
                    </el-form-item>
                    <el-form-item label="新积分">
                        <el-input-number v-model="pointsForm.newPoints" :min="0" :max="1000000"></el-input-number>
                    </el-form-item>
                </el-form>
                <template #footer>
                    <span class="dialog-footer">
                        <el-button @click="pointsDialogVisible = false">取消</el-button>
                        <el-button type="primary" @click="updatePoints">保存</el-button>
                    </span>
                </template>
            </el-dialog>
        </div>
    `
}; 