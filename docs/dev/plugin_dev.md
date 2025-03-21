# 插件开发指南

XBotV2的一个核心特性是其高度可扩展的插件系统。通过开发插件，您可以为机器人添加自定义功能，而无需修改核心代码。本指南将帮助您了解如何创建、测试和发布自己的XBotV2插件。

## 插件基础知识

### 插件目录结构

一个典型的XBotV2插件应该具有以下目录结构：

```
plugins/
└── MyPlugin/
    ├── __init__.py    # 插件入口文件
    ├── info.json      # 插件元数据
    └── config.toml    # 插件配置文件
```

其中：
- `__init__.py`：包含插件的主类和业务逻辑
- `info.json`：定义插件的基本信息，如名称、版本、作者等
- `config.toml`：存储插件的配置参数

### 插件生命周期

XBotV2插件有以下生命周期事件：

1. **加载**：系统扫描插件目录并发现插件
2. **初始化**：调用插件的`initialize`方法，传入配置
3. **启用**：调用插件的`on_enable`方法
4. **运行**：插件处理各种事件（消息、指令等）
5. **禁用**：调用插件的`on_disable`方法
6. **卸载**：从系统中移除插件

## 创建第一个插件

下面，我们将创建一个简单的"Echo"插件，它可以重复用户发送的消息。

### 1. 创建插件目录

在`plugins`目录下创建一个名为`Echo`的文件夹：

```bash
mkdir -p plugins/Echo
```

### 2. 定义插件元数据

创建`plugins/Echo/info.json`文件，内容如下：

```json
{
  "name": "Echo回声",
  "version": "1.0.0",
  "description": "一个简单的回声插件，重复用户发送的消息",
  "author": "xiaoxinkeji",
  "email": "3264913523@qq.com",
  "url": "https://github.com/xiaoxinkeji/xbotv2-echo-plugin",
  "tags": ["示例", "工具"],
  "requirements": []
}
```

### 3. 创建配置文件

创建`plugins/Echo/config.toml`文件，内容如下：

```toml
[general]
enabled = true          # 是否启用插件
command_prefix = "echo" # 触发命令前缀

[settings]
reply_prefix = "你说："  # 回复前缀
ignore_case = true      # 是否忽略大小写
```

### 4. 编写插件代码

创建`plugins/Echo/.__init__.py`文件，内容如下：

```python
import asyncio
from loguru import logger

class Echo:
    def __init__(self, bot):
        """初始化插件"""
        self.bot = bot
        self.name = "Echo"
        self.config = None
        logger.info("Echo插件已加载")
    
    async def initialize(self, config):
        """初始化插件配置"""
        self.config = config
        logger.info("Echo插件已初始化")
        return True
    
    async def on_message(self, message):
        """处理接收到的消息"""
        # 获取消息内容
        content = message.get("content", "")
        
        # 检查是否包含触发命令
        command_prefix = self.config["general"]["command_prefix"]
        
        if self.config["settings"]["ignore_case"]:
            has_prefix = content.lower().startswith(command_prefix.lower())
        else:
            has_prefix = content.startswith(command_prefix)
        
        if has_prefix:
            # 提取命令后的文本
            echo_text = content[len(command_prefix):].strip()
            
            # 如果有文本要回显
            if echo_text:
                # 构建回复
                reply_prefix = self.config["settings"]["reply_prefix"]
                reply = f"{reply_prefix}{echo_text}"
                
                # 发送回复
                sender = message["sender"]
                await self.bot.send_text_message(sender, reply)
                logger.info(f"已回显消息: {echo_text}")
    
    async def on_enable(self):
        """插件启用时调用"""
        logger.info("Echo插件已启用")
        return True
    
    async def on_disable(self):
        """插件禁用时调用"""
        logger.info("Echo插件已禁用")
        return True

# 必须定义Plugin类，作为插件的入口点
Plugin = Echo
```

## 插件API参考

### 核心事件处理器

XBotV2插件可以实现以下事件处理方法：

```python
async def on_message(self, message):
    """处理普通消息"""
    pass

async def on_friend_request(self, request):
    """处理好友请求"""
    pass

async def on_payment_request(self, request):
    """处理支付请求"""
    pass

async def on_chatroom_invite(self, invite):
    """处理群聊邀请"""
    pass

async def on_timer(self, timestamp):
    """定时器事件，每分钟触发一次"""
    pass
```

### 常用API方法

XBotV2提供了丰富的API，以下是一些常用方法：

#### 消息相关

```python
# 发送文本消息
await self.bot.send_text_message(receiver_id, "你好")

# 发送图片消息
await self.bot.send_image_message(receiver_id, "path/to/image.jpg")

# 发送语音消息
await self.bot.send_voice_message(receiver_id, "path/to/voice.mp3", length_ms=1000)

# 发送视频消息
await self.bot.send_video_message(receiver_id, "path/to/video.mp4")

# 发送链接卡片
await self.bot.send_link_message(
    receiver_id,
    title="标题",
    description="描述",
    url="https://example.com",
    image_url="https://example.com/image.jpg"
)

# 撤回消息
await self.bot.revoke_message(message_id)
```

#### 群聊相关

```python
# 获取群信息
group_info = await self.bot.get_chatroom_info(chatroom_id)

# 获取群成员列表
members = await self.bot.get_chatroom_member_list(chatroom_id)

# 邀请用户加入群聊
await self.bot.invite_chatroom_member(chatroom_id, user_id)

# 移除群成员
await self.bot.delete_chatroom_member(chatroom_id, user_id)
```

#### 好友相关

```python
# 获取联系人信息
contact = await self.bot.get_contact(user_id)

# 获取联系人列表
contacts = await self.bot.get_contract_list()

# 接受好友请求
await self.bot.accept_friend(v3, v4)
```

## 高级开发技巧

### 1. 插件依赖管理

如果您的插件需要第三方库，请在`info.json`的`requirements`字段中列出：

```json
"requirements": [
  "requests>=2.25.0",
  "beautifulsoup4>=4.9.3"
]
```

XBotV2会在安装插件时自动安装这些依赖。

### 2. 异步编程

XBotV2使用Python的异步编程模型。确保您的代码正确使用`async`/`await`语法：

```python
async def some_method(self):
    # 不要使用time.sleep()，它会阻塞整个程序
    # 使用asyncio.sleep()代替
    await asyncio.sleep(1)
    
    # 调用异步API方法
    await self.bot.send_text_message(receiver_id, "消息")
```

### 3. 数据持久化

对于需要保存数据的插件，您可以使用XBotV2提供的数据库接口：

```python
from database.keyvalDB import KeyValDB

# 创建键值存储
storage = KeyValDB("my_plugin_data")

# 存储数据
await storage.set("key", "value")

# 读取数据
value = await storage.get("key")
```

### 4. 错误处理

始终在插件中添加适当的错误处理：

```python
async def on_message(self, message):
    try:
        # 您的代码
        pass
    except Exception as e:
        logger.error(f"处理消息时出错: {e}")
        # 可选：发送错误通知给管理员
        admin_id = self.config.get("admin_id")
        if admin_id:
            await self.bot.send_text_message(admin_id, f"插件错误: {e}")
```

## 测试与调试

### 日志调试

使用`loguru.logger`记录信息，帮助调试：

```python
from loguru import logger

# 不同级别的日志
logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误")
```

日志文件位于项目根目录的`logs`文件夹中。

### 测试模式

在开发插件时，您可以启用XBotV2的调试模式，方法是修改`main_config.toml`：

```toml
[WebInterface]
debug = true
```

这将提供更详细的错误信息和实时日志。

## 发布插件

当您的插件开发完成后，可以通过以下方式分享：

1. **GitHub仓库**：创建一个公共仓库，上传您的插件代码
2. **XBotV2插件市场**：联系项目维护者，将您的插件添加到官方插件市场

### 插件发布检查清单

在发布前，请确保：

- [ ] 插件功能完整且正常工作
- [ ] 代码中没有敏感信息（如API密钥）
- [ ] `info.json`中的信息准确完整
- [ ] 提供了清晰的文档和使用说明
- [ ] 正确处理了可能的错误情况
- [ ] 已在多种环境中测试

## 示例插件

以下是一些可供参考的示例插件：

- [天气查询插件](https://github.com/xiaoxinkeji/xbotv2-weather-plugin)
- [每日新闻插件](https://github.com/xiaoxinkeji/xbotv2-news-plugin)
- [翻译插件](https://github.com/xiaoxinkeji/xbotv2-translate-plugin)

## 插件开发社区

加入我们的开发者社区，与其他插件开发者交流：

- GitHub讨论区: [https://github.com/xiaoxinkeji/xbotv2/discussions](https://github.com/xiaoxinkeji/xbotv2/discussions)
- 开发者交流群: [添加方式](https://example.com/join-dev-group)

---

祝您的插件开发之旅愉快！如有任何问题，请随时在社区中提问或提交问题。 