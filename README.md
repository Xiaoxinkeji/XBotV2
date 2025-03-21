# 🤖 XBotV2

> **注意**：本项目是基于 [HenryXiaoYang/XYBotV2](https://github.com/HenryXiaoYang/XYBotV2) 二次开发的微信机器人框架。特此鸣谢原项目作者的贡献和支持。

XBotV2 是一个功能丰富的微信机器人框架，支持多种互动功能和游戏玩法。

## 项目简介

XBotV2是一个功能强大的微信机器人框架，基于Python开发，提供了丰富的API和插件系统，让用户可以轻松实现微信消息的自动化处理和智能回复。项目特点包括高度定制化的插件系统、直观的Web管理界面、稳定的消息处理机制以及完善的开发接口。

**核心特性：**

- 完整的微信API封装，支持文本、图片、语音、视频等多种消息类型
- 灵活的插件系统，支持热插拔和动态管理
- 用户友好的Web管理界面
- 完备的日志和状态监控
- 支持Docker部署，便于跨平台使用
- 可扩展的架构设计，便于二次开发

## 入门指南

### 系统要求

- Python 3.11+
- Redis服务器
- 支持的操作系统：Windows、macOS、Linux

### 安装方法

#### 方法一：Docker安装（推荐）

1. 确保已安装Docker和Docker Compose
2. 克隆仓库：
   ```bash
   git clone https://github.com/xiaoxinkeji/xbotv2.git
   cd xbotv2
   ```
3. 启动容器：
   ```bash
   docker-compose up -d
   ```
4. 访问Web界面：`http://localhost:8080`，默认账号密码：admin/admin123

#### 方法二：手动安装

1. 确保系统已安装Python 3.11及以上版本
2. 安装并启动Redis服务
3. 克隆仓库：
   ```bash
   git clone https://github.com/xiaoxinkeji/xbotv2.git
   cd xbotv2
   ```
4. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
5. 启动程序：
   ```bash
   python main.py
   ```
6. 访问Web界面：`http://localhost:8080`，默认账号密码：admin/admin123

### 首次配置

1. 登录Web管理界面
2. 修改默认管理员密码（设置页面）
3. 配置微信登录（微信登录页面）
4. 安装并启用需要的插件（插件管理页面）

## 基本使用

### 微信登录

1. 在Web界面中点击"微信登录"
2. 选择登录方式：
   - 扫码登录：扫描页面显示的二维码
   - 唤醒登录：如果之前已登录过，可以尝试唤醒恢复会话
3. 登录成功后，机器人状态会显示为"在线"

### 插件管理

1. 在Web界面中点击"插件管理"
2. 已安装的插件会显示在列表中，可以：
   - 启用/禁用插件
   - 配置插件参数
   - 卸载插件
3. 安装新插件：
   - 点击"安装插件"按钮
   - 选择安装方式：Git仓库、本地文件、插件市场
   - 填写相关信息后安装

### 消息处理流程

XBotV2处理消息的基本流程：

1. 接收微信消息
2. 过滤消息（根据配置的黑白名单）
3. 分发消息到已启用的插件
4. 插件处理消息并可能产生回复
5. 发送回复到微信

## 系统架构

XBotV2采用模块化设计，主要组件包括：

1. **WechatAPI模块**：负责与微信服务器通信，处理消息收发
2. **核心引擎**：负责消息路由和插件管理
3. **插件系统**：提供扩展功能的接口
4. **数据库**：存储配置、消息记录和其他数据
5. **Web界面**：提供可视化管理功能

### 目录结构

```
xbotv2/
├── database/            # 数据库相关代码
│   ├── XYBotDB.py       # 主数据库
│   ├── keyvalDB.py      # 键值存储
│   ├── messsagDB.py     # 消息数据库
│   └── plugin_repository.py # 插件仓库
├── docs/                # 文档
├── logs/                # 日志文件
├── plugins/             # 插件目录
├── resource/            # 资源文件
├── utils/               # 工具函数
├── WechatAPI/           # 微信API库
├── web/                 # Web界面
│   ├── static/          # 静态资源
│   └── templates/       # 页面模板
├── bot_core.py          # 机器人核心
├── main.py              # 主程序
├── main_config.toml     # 主配置文件
├── requirements.txt     # 依赖列表
└── docker-compose.yml   # Docker配置
```

## 配置详解

### 主配置文件(main_config.toml)

主配置文件包含以下关键部分：

#### WechatAPIServer配置

```toml
[WechatAPIServer]
port = 9000                # WechatAPI服务器端口
mode = "release"           # 运行模式：release/debug
redis-host = "127.0.0.1"   # Redis地址
redis-port = 6379          # Redis端口
redis-password = ""        # Redis密码
redis-db = 0               # Redis数据库编号
```

#### XYBot核心配置

```toml
[XYBot]
version = "v1.0.0"                    # 版本号
ignore-protection = false             # 是否忽略风控保护
admins = ["admin-wxid"]               # 管理员微信ID列表
disabled-plugins = ["ExamplePlugin"]  # 禁用的插件列表
timezone = "Asia/Shanghai"            # 时区设置
auto-restart = false                  # 自动重启功能
```

#### Web界面配置

```toml
[WebInterface]
enable = true                 # 是否启用Web界面
port = 8080                   # Web界面端口
host = "0.0.0.0"              # 绑定地址
debug = false                 # 调试模式
username = "admin"            # 管理员用户名
password = "admin123"         # 管理员密码
```

#### 消息过滤配置

```toml
ignore-mode = "None"          # 消息处理模式：None/Whitelist/Blacklist
whitelist = ["wxid_1", "111@chatroom"]  # 白名单
blacklist = ["wxid_3", "333@chatroom"]  # 黑名单
```

## 插件开发指南

### 插件基本结构

每个插件应该包含以下文件：

- `__init__.py`：插件入口
- `info.json`：插件元数据
- `config.toml`：插件配置

### 插件元数据(info.json)

```json
{
  "name": "示例插件",
  "version": "1.0.0",
  "description": "这是一个示例插件",
  "author": "开发者名称",
  "email": "开发者邮箱",
  "url": "https://github.com/example/plugin",
  "tags": ["示例", "教程"],
  "requirements": ["requests>=2.25.0"],
  "permissions": ["message_read", "message_send"]
}
```

### 插件配置(config.toml)

```toml
[general]
enabled = true           # 是否启用
command_prefix = "!"     # 命令前缀

[settings]
reply_all = false        # 示例设置
custom_text = "你好世界"  # 示例设置
```

### 插件开发示例

创建一个简单的"你好世界"插件：

1. 创建目录结构：
   ```
   plugins/HelloWorld/
   ├── __init__.py
   ├── info.json
   └── config.toml
   ```

2. 编辑`info.json`：
   ```json
   {
     "name": "你好世界",
     "version": "1.0.0",
     "description": "一个简单的示例插件",
     "author": "XBotV2团队",
     "tags": ["示例"],
     "requirements": []
   }
   ```

3. 编辑`config.toml`：
   ```toml
   [general]
   enabled = true
   
   [settings]
   trigger_word = "你好"
   reply_text = "世界你好！"
   ```

4. 编辑`__init__.py`：
   ```python
   import asyncio
   from loguru import logger
   
   class HelloWorld:
       def __init__(self, bot):
           self.bot = bot
           self.name = "HelloWorld"
           self.config = None
       
       async def initialize(self, config):
           """初始化插件"""
           self.config = config
           logger.info("你好世界插件已初始化")
           return True
       
       async def on_message(self, message):
           """处理消息事件"""
           # 检查消息是否包含触发词
           if self.config["settings"]["trigger_word"] in message["content"]:
               # 获取发送者信息
               sender = message["sender"]
               # 构建回复
               reply_text = self.config["settings"]["reply_text"]
               # 发送回复
               await self.bot.send_text_message(sender, reply_text)
               logger.info(f"已回复消息: {reply_text}")
       
       async def on_disable(self):
           """插件被禁用时调用"""
           logger.info("你好世界插件已禁用")
           return True
       
       async def on_enable(self):
           """插件被启用时调用"""
           logger.info("你好世界插件已启用")
           return True
   
   # 插件主类，必须命名为Plugin
   Plugin = HelloWorld
   ```

### 插件生命周期

1. **加载**：插件被发现并加载到内存
2. **初始化**：调用`initialize`方法，传入配置
3. **启用**：调用`on_enable`方法
4. **运行**：处理各种事件（消息、好友请求等）
5. **禁用**：调用`on_disable`方法
6. **卸载**：从内存中移除插件

### 插件API参考

XBotV2提供了丰富的API，可以在插件中使用：

#### 消息相关

```python
# 发送文本消息
await self.bot.send_text_message(receiver, "你好")

# 发送图片消息
await self.bot.send_image_message(receiver, "path/to/image.jpg")

# 发送语音消息
await self.bot.send_voice_message(receiver, "path/to/voice.mp3")

# 发送视频消息
await self.bot.send_video_message(receiver, "path/to/video.mp4")

# 发送链接消息
await self.bot.send_link_message(receiver, "标题", "描述", "url", "图片url")

# 撤回消息
await self.bot.revoke_message(msgid)
```

#### 群聊相关

```python
# 获取群聊信息
group_info = await self.bot.get_chatroom_info(chatroom_id)

# 获取群聊成员列表
members = await self.bot.get_chatroom_member_list(chatroom_id)

# 邀请成员加入群聊
await self.bot.invite_chatroom_member(chatroom_id, wxid)
```

#### 好友相关

```python
# 获取联系人信息
contact = await self.bot.get_contact(wxid)

# 获取联系人列表
contacts = await self.bot.get_contract_list()

# 接受好友请求
await self.bot.accept_friend(v3, v4)
```

## 插件市场

XBotV2提供了插件市场功能，用户可以浏览、下载和安装其他开发者贡献的插件。

### 使用插件市场

1. 在Web界面中点击"插件管理"，然后点击"插件市场"
2. 浏览可用插件，可以根据类别筛选或搜索
3. 点击插件卡片查看详情
4. 点击"安装"按钮开始安装
5. 安装完成后可以在插件管理页面启用和配置

### 发布插件到市场

要发布自己的插件到市场，需要：

1. 将插件代码推送到GitHub仓库
2. 确保仓库包含完整的插件结构和有效的info.json
3. 将仓库URL提交到插件市场（联系管理员）

## API参考文档

### WechatAPI

XBotV2使用WechatAPI与微信通信，主要类包括：

#### WechatAPIClient

主要方法：

- `login`相关：
  - `is_running()`: 检查API服务是否运行
  - `get_qr_code()`: 获取登录二维码
  - `check_login_uuid()`: 检查登录状态
  - `awaken_login()`: 唤醒登录
  - `log_out()`: 退出登录
  - `heartbeat()`: 发送心跳包

- `message`相关：
  - `sync_message()`: 同步消息
  - `send_text_message()`: 发送文本消息
  - `send_image_message()`: 发送图片消息
  - `send_voice_message()`: 发送语音消息
  - `send_video_message()`: 发送视频消息
  - `send_link_message()`: 发送链接消息
  - `send_card_message()`: 发送名片消息
  - `send_app_message()`: 发送应用消息
  - `revoke_message()`: 撤回消息

- `user`相关：
  - `get_profile()`: 获取个人信息
  - `is_logged_in()`: 检查是否已登录

- `chatroom`相关：
  - `get_chatroom_info()`: 获取群聊信息
  - `get_chatroom_member_list()`: 获取群成员列表
  - `add_chatroom_member()`: 添加群成员
  - `invite_chatroom_member()`: 邀请群成员

- `friend`相关：
  - `get_contact()`: 获取联系人信息
  - `get_contract_list()`: 获取联系人列表
  - `accept_friend()`: 接受好友请求

- `工具`相关：
  - `download_image()`: 下载图片
  - `download_video()`: 下载视频
  - `download_voice()`: 下载语音
  - `download_attach()`: 下载附件

## 常见问题解答

### 运行问题

**Q: 程序启动后提示Redis连接失败怎么办？**  
A: 请检查Redis服务是否已启动，并确认配置文件中的Redis连接信息正确。

**Q: 微信扫码登录后没有反应怎么办？**  
A: 请检查网络连接，确保防火墙没有阻止相关端口。如果使用Docker，确保端口映射正确。

**Q: 更新后程序无法启动怎么办？**  
A: 检查是否满足新版本的依赖要求，尝试重新安装依赖 `pip install -r requirements.txt`。

### 插件问题

**Q: 安装插件时提示依赖错误怎么办？**  
A: 手动安装插件所需的依赖，或者检查插件是否与当前XBotV2版本兼容。

**Q: 为什么有些插件无法启用？**  
A: 可能原因：
1. 插件与当前版本不兼容
2. 插件依赖未满足
3. 插件配置有误
4. 插件文件结构不正确

**Q: 如何修复插件配置？**  
A: 在Web界面中，进入插件配置页面，重置为默认配置或手动修改配置文件。

### 其他问题

**Q: 如何备份XBotV2数据？**  
A: 备份以下目录：
- `database/` - 数据库文件
- `plugins/` - 已安装的插件
- `resource/` - 资源文件
- `main_config.toml` - 主配置文件

**Q: 如何将XBotV2迁移到新服务器？**  
A: 1. 安装XBotV2到新服务器  
   2. 复制上述备份数据到对应目录  
   3. 重启XBotV2

## 联系与支持

- GitHub: [https://github.com/xiaoxinkeji](https://github.com/xiaoxinkeji)
- 问题反馈: [https://github.com/xiaoxinkeji/xbotv2/issues](https://github.com/xiaoxinkeji/xbotv2/issues)
- 电子邮件: [3264913523@qq.com](mailto:3264913523@qq.com)

## 贡献指南

我们欢迎各种形式的贡献，包括但不限于：

- 代码贡献
- 文档改进
- 问题报告
- 功能建议
- 插件开发

详细贡献流程请参考仓库中的`CONTRIBUTING.md`文件。

## 许可证

XBotV2采用[MIT许可证](https://opensource.org/licenses/MIT)。

---

© 2025-2026 XBotV2团队。保留所有权利。