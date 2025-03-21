# API参考文档

本文档详细介绍XBotV2提供的API接口，供插件开发者和二次开发者使用。XBotV2采用异步编程模型，大部分API函数都是异步的，需要使用`async/await`语法调用。

## 核心API

核心API是插件开发中最常用的接口，提供了与微信交互的基本功能。这些API通过插件初始化时传入的`bot`对象访问。

### 消息发送

#### 发送文本消息

```python
async def send_text_message(receiver_id: str, content: str) -> dict:
    """
    发送文本消息
    
    参数:
        receiver_id (str): 接收者ID，可以是个人wxid或群聊ID
        content (str): 消息内容
        
    返回:
        dict: 包含发送结果的字典，包含字段：success, message_id, error_msg等
    """
```

示例：
```python
result = await self.bot.send_text_message("wxid_abc123", "你好！")
if result["success"]:
    logger.info(f"消息已发送，ID: {result['message_id']}")
else:
    logger.error(f"消息发送失败: {result['error_msg']}")
```

#### 发送图片消息

```python
async def send_image_message(receiver_id: str, image_path: str) -> dict:
    """
    发送图片消息
    
    参数:
        receiver_id (str): 接收者ID
        image_path (str): 图片路径，可以是本地路径或URL
        
    返回:
        dict: 包含发送结果的字典
    """
```

示例：
```python
# 发送本地图片
result = await self.bot.send_image_message("wxid_abc123", "resource/images/hello.jpg")

# 发送网络图片
result = await self.bot.send_image_message("wxid_abc123", "https://example.com/image.jpg")
```

#### 发送语音消息

```python
async def send_voice_message(receiver_id: str, voice_path: str, length_ms: int = 0) -> dict:
    """
    发送语音消息
    
    参数:
        receiver_id (str): 接收者ID
        voice_path (str): 语音文件路径，支持.mp3、.silk格式
        length_ms (int): 语音长度(毫秒)，如果为0会自动计算
        
    返回:
        dict: 包含发送结果的字典
    """
```

示例：
```python
result = await self.bot.send_voice_message("wxid_abc123", "resource/voice/greeting.mp3", 3000)
```

#### 发送视频消息

```python
async def send_video_message(receiver_id: str, video_path: str) -> dict:
    """
    发送视频消息
    
    参数:
        receiver_id (str): 接收者ID
        video_path (str): 视频文件路径
        
    返回:
        dict: 包含发送结果的字典
    """
```

示例：
```python
result = await self.bot.send_video_message("wxid_abc123", "resource/videos/demo.mp4")
```

#### 发送链接消息

```python
async def send_link_message(
    receiver_id: str, 
    title: str, 
    description: str, 
    url: str, 
    image_url: str = ""
) -> dict:
    """
    发送链接卡片消息
    
    参数:
        receiver_id (str): 接收者ID
        title (str): 卡片标题
        description (str): 卡片描述
        url (str): 链接URL
        image_url (str): 卡片图片URL，可选
        
    返回:
        dict: 包含发送结果的字典
    """
```

示例：
```python
result = await self.bot.send_link_message(
    "wxid_abc123",
    "XBotV2项目",
    "一个强大的微信机器人框架",
    "https://github.com/xiaoxinkeji/xbotv2",
    "https://example.com/preview.jpg"
)
```

#### 发送文件消息

```python
async def send_file_message(receiver_id: str, file_path: str) -> dict:
    """
    发送文件消息
    
    参数:
        receiver_id (str): 接收者ID
        file_path (str): 文件路径
        
    返回:
        dict: 包含发送结果的字典
    """
```

示例：
```python
result = await self.bot.send_file_message("wxid_abc123", "resource/files/document.pdf")
```

#### 撤回消息

```python
async def revoke_message(message_id: str) -> dict:
    """
    撤回消息
    
    参数:
        message_id (str): 要撤回的消息ID
        
    返回:
        dict: 包含操作结果的字典
    """
```

示例：
```python
result = await self.bot.revoke_message("123456789012345")
```

### 联系人相关

#### 获取联系人信息

```python
async def get_contact(wxid: str) -> dict:
    """
    获取联系人信息
    
    参数:
        wxid (str): 联系人wxid
        
    返回:
        dict: 联系人信息字典，包含字段如:
            - wxid: 微信ID
            - nickname: 昵称
            - remark: 备注名
            - avatar: 头像URL
            - v1: v1值(仅好友)
    """
```

示例：
```python
contact = await self.bot.get_contact("wxid_abc123")
if contact:
    logger.info(f"联系人昵称: {contact['nickname']}")
```

#### 获取联系人列表

```python
async def get_contact_list() -> list:
    """
    获取联系人列表
    
    返回:
        list: 联系人信息列表
    """
```

示例：
```python
contacts = await self.bot.get_contact_list()
logger.info(f"共有 {len(contacts)} 个联系人")
```

#### 接受好友请求

```python
async def accept_friend(v1: str, v2: str, scene: int = 0) -> dict:
    """
    接受好友请求
    
    参数:
        v1 (str): 好友请求v1值
        v2 (str): 好友请求v2值
        scene (int): 场景值
        
    返回:
        dict: 操作结果
    """
```

示例：
```python
# 在on_friend_request事件中使用
async def on_friend_request(self, request):
    result = await self.bot.accept_friend(request["v1"], request["v2"])
    if result["success"]:
        logger.info("已接受好友请求")
```

### 群聊相关

#### 获取群聊信息

```python
async def get_chatroom_info(chatroom_id: str) -> dict:
    """
    获取群聊信息
    
    参数:
        chatroom_id (str): 群聊ID
        
    返回:
        dict: 群聊信息字典
    """
```

示例：
```python
group = await self.bot.get_chatroom_info("12345678@chatroom")
logger.info(f"群名称: {group['name']}, 成员数: {len(group['member_list'])}")
```

#### 获取群成员列表

```python
async def get_chatroom_member_list(chatroom_id: str) -> list:
    """
    获取群成员列表
    
    参数:
        chatroom_id (str): 群聊ID
        
    返回:
        list: 群成员ID列表
    """
```

示例：
```python
members = await self.bot.get_chatroom_member_list("12345678@chatroom")
logger.info(f"群成员数量: {len(members)}")
```

#### 获取群成员昵称

```python
async def get_chatroom_member_nickname(chatroom_id: str, member_id: str) -> str:
    """
    获取群成员在群内的昵称
    
    参数:
        chatroom_id (str): 群聊ID
        member_id (str): 成员wxid
        
    返回:
        str: 群内昵称
    """
```

示例：
```python
nickname = await self.bot.get_chatroom_member_nickname("12345678@chatroom", "wxid_abc123")
logger.info(f"群内昵称: {nickname}")
```

#### 邀请成员加入群聊

```python
async def invite_chatroom_member(chatroom_id: str, wxid: str) -> dict:
    """
    邀请成员加入群聊
    
    参数:
        chatroom_id (str): 群聊ID
        wxid (str): 待邀请成员的wxid
        
    返回:
        dict: 操作结果
    """
```

示例：
```python
result = await self.bot.invite_chatroom_member("12345678@chatroom", "wxid_abc123")
```

#### 删除群成员

```python
async def delete_chatroom_member(chatroom_id: str, wxid: str) -> dict:
    """
    从群聊中删除成员
    
    参数:
        chatroom_id (str): 群聊ID
        wxid (str): 待删除成员的wxid
        
    返回:
        dict: 操作结果
    """
```

示例：
```python
result = await self.bot.delete_chatroom_member("12345678@chatroom", "wxid_abc123")
```

### 文件与媒体

#### 下载图片

```python
async def download_image(message_id: str, save_path: str = None) -> str:
    """
    下载图片
    
    参数:
        message_id (str): 消息ID
        save_path (str): 保存路径，默认为临时目录
        
    返回:
        str: 图片保存路径
    """
```

示例：
```python
async def on_message(self, message):
    if message["type"] == 3:  # 图片消息
        image_path = await self.bot.download_image(message["id"], "resource/images/received.jpg")
        logger.info(f"图片已保存至: {image_path}")
```

#### 下载语音

```python
async def download_voice(message_id: str, save_path: str = None) -> str:
    """
    下载语音
    
    参数:
        message_id (str): 消息ID
        save_path (str): 保存路径，默认为临时目录
        
    返回:
        str: 语音保存路径
    """
```

示例：
```python
voice_path = await self.bot.download_voice(message["id"])
```

#### 下载视频

```python
async def download_video(message_id: str, save_path: str = None) -> str:
    """
    下载视频
    
    参数:
        message_id (str): 消息ID
        save_path (str): 保存路径，默认为临时目录
        
    返回:
        str: 视频保存路径
    """
```

示例：
```python
video_path = await self.bot.download_video(message["id"])
```

#### 下载文件

```python
async def download_file(message_id: str, save_path: str = None) -> str:
    """
    下载文件
    
    参数:
        message_id (str): 消息ID
        save_path (str): 保存路径，默认为临时目录
        
    返回:
        str: 文件保存路径
    """
```

示例：
```python
file_path = await self.bot.download_file(message["id"])
```

### 系统控制

#### 获取登录状态

```python
async def is_logged_in() -> bool:
    """
    检查是否已登录
    
    返回:
        bool: 登录状态
    """
```

示例：
```python
if await self.bot.is_logged_in():
    logger.info("机器人已登录")
else:
    logger.warning("机器人未登录")
```

#### 获取个人信息

```python
async def get_self_info() -> dict:
    """
    获取当前登录帐号的个人信息
    
    返回:
        dict: 个人信息字典
    """
```

示例：
```python
info = await self.bot.get_self_info()
logger.info(f"当前帐号: {info['nickname']} ({info['wxid']})")
```

#### 退出登录

```python
async def logout() -> dict:
    """
    退出当前登录
    
    返回:
        dict: 操作结果
    """
```

示例：
```python
result = await self.bot.logout()
```

## 数据存储API

XBotV2提供了数据存储API，帮助插件进行数据持久化。这些API可以通过导入相应模块使用。

### 键值存储

键值存储API适用于简单的数据持久化需求。

```python
from database.keyvalDB import KeyValDB

# 创建一个存储实例，"my_plugin"是命名空间，确保数据隔离
storage = KeyValDB("my_plugin")
```

#### 存储数据

```python
async def set(key: str, value: any) -> bool:
    """
    存储键值对
    
    参数:
        key (str): 键名
        value (any): 值，支持任何可JSON序列化的对象
        
    返回:
        bool: 操作是否成功
    """
```

示例：
```python
await storage.set("user_count", 42)
await storage.set("settings", {"theme": "dark", "notification": True})
```

#### 获取数据

```python
async def get(key: str, default: any = None) -> any:
    """
    获取键对应的值
    
    参数:
        key (str): 键名
        default (any): 如果键不存在，返回的默认值
        
    返回:
        any: 键对应的值或默认值
    """
```

示例：
```python
count = await storage.get("user_count", 0)
settings = await storage.get("settings", {})
```

#### 删除数据

```python
async def delete(key: str) -> bool:
    """
    删除键值对
    
    参数:
        key (str): 键名
        
    返回:
        bool: 操作是否成功
    """
```

示例：
```python
success = await storage.delete("temp_data")
```

#### 检查键是否存在

```python
async def exists(key: str) -> bool:
    """
    检查键是否存在
    
    参数:
        key (str): 键名
        
    返回:
        bool: 键是否存在
    """
```

示例：
```python
if await storage.exists("user_settings"):
    # 处理已存在的设置
    pass
```

#### 增加数值

```python
async def increment(key: str, amount: int = 1) -> int:
    """
    增加数值
    
    参数:
        key (str): 键名
        amount (int): 增加的数量
        
    返回:
        int: 增加后的值
    """
```

示例：
```python
new_count = await storage.increment("visitor_count")
new_score = await storage.increment("user_score", 10)
```

### 消息数据库

消息数据库API用于存储和查询消息历史记录。

```python
from database.messageDB import MessageDB

# 获取消息数据库实例
message_db = MessageDB()
```

#### 存储消息

```python
async def save_message(message: dict) -> bool:
    """
    保存消息记录
    
    参数:
        message (dict): 消息字典
        
    返回:
        bool: 操作是否成功
    """
```

示例：
```python
await message_db.save_message({
    "id": "123456789",
    "type": 1,
    "sender": "wxid_abc123",
    "content": "你好",
    "timestamp": 1673456789
})
```

#### 查询消息

```python
async def query_messages(
    sender: str = None,
    receiver: str = None,
    start_time: int = None,
    end_time: int = None,
    limit: int = 100,
    offset: int = 0
) -> list:
    """
    查询消息记录
    
    参数:
        sender (str): 发送者ID
        receiver (str): 接收者ID
        start_time (int): 开始时间戳
        end_time (int): 结束时间戳
        limit (int): 结果限制数量
        offset (int): 结果偏移量
        
    返回:
        list: 消息列表
    """
```

示例：
```python
# 获取最近与特定用户的100条消息
messages = await message_db.query_messages(
    sender="wxid_abc123",
    limit=100
)

# 获取过去24小时的所有消息
import time
end = int(time.time())
start = end - 86400
messages = await message_db.query_messages(
    start_time=start,
    end_time=end
)
```

## Web API

Web API提供了与Web界面交互的接口，主要用于系统控制和状态查询。

### 获取机器人状态

```python
GET /api/status
```

响应：
```json
{
  "status": "online",
  "wxid": "wxid_abc123",
  "nickname": "机器人",
  "startup_time": 1673456789,
  "message_count": 1234,
  "plugins": {
    "active": 10,
    "total": 15
  }
}
```

### 插件管理API

#### 获取插件列表

```python
GET /api/plugins
```

响应：
```json
[
  {
    "name": "Echo",
    "display_name": "回声",
    "version": "1.0.0",
    "author": "XBotV2团队",
    "description": "简单的回声插件",
    "enabled": true
  },
  {
    "name": "Weather",
    "display_name": "天气查询",
    "version": "1.2.0",
    "author": "XBotV2团队",
    "description": "天气查询插件",
    "enabled": false
  }
]
```

#### 启用/禁用插件

```python
POST /api/plugins/{plugin_name}/toggle
```

请求体：
```json
{
  "enabled": true
}
```

响应：
```json
{
  "success": true,
  "message": "插件已启用"
}
```

#### 更新插件配置

```python
POST /api/plugins/{plugin_name}/config
```

请求体：
```json
{
  "settings": {
    "reply_prefix": "回复: ",
    "ignore_case": true
  }
}
```

响应：
```json
{
  "success": true,
  "message": "配置已更新"
}
```

### 系统设置API

#### 获取系统设置

```python
GET /api/settings
```

响应：
```json
{
  "WechatAPIServer": {
    "port": 9000,
    "mode": "release"
  },
  "XYBot": {
    "version": "v1.0.0",
    "admins": ["wxid_admin123"]
  },
  "WebInterface": {
    "port": 8080,
    "debug": false
  }
}
```

#### 更新系统设置

```python
POST /api/settings
```

请求体：
```json
{
  "XYBot": {
    "admins": ["wxid_admin123", "wxid_new456"]
  }
}
```

响应：
```json
{
  "success": true,
  "message": "设置已更新"
}
```

## 插件市场API

#### 获取插件列表

```python
GET /api/plugin_marketplace
```

参数：
- `category`: 分类筛选
- `keyword`: 关键词搜索
- `sort`: 排序方式
- `page`: 页码
- `page_size`: 每页数量

响应：
```json
{
  "total": 42,
  "page": 1,
  "page_size": 10,
  "plugins": [
    {
      "id": "weather",
      "name": "天气查询",
      "description": "查询全国天气",
      "version": "1.0.0",
      "author": "XBotV2团队",
      "downloads": 1234,
      "rating": 4.8,
      "category": "工具",
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-06-01T00:00:00Z"
    },
    ...
  ]
}
```

#### 获取插件详情

```python
GET /api/plugin_marketplace/{plugin_id}
```

响应：
```json
{
  "id": "weather",
  "name": "天气查询",
  "description": "查询全国天气",
  "long_description": "这是一个功能强大的天气查询插件，支持...",
  "version": "1.0.0",
  "author": "XBotV2团队",
  "email": "dev@example.com",
  "url": "https://github.com/xbotv2/weather-plugin",
  "downloads": 1234,
  "rating": 4.8,
  "ratings_count": 56,
  "category": "工具",
  "tags": ["天气", "实用工具"],
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-06-01T00:00:00Z",
  "versions": [
    {
      "version": "1.0.0",
      "release_notes": "初始版本",
      "created_at": "2023-01-01T00:00:00Z"
    },
    {
      "version": "0.9.0",
      "release_notes": "测试版",
      "created_at": "2022-12-01T00:00:00Z"
    }
  ],
  "requirements": [
    "requests>=2.25.0"
  ],
  "screenshots": [
    "https://example.com/weather/screenshot1.jpg"
  ]
}
```

#### 安装插件

```python
POST /api/plugin_marketplace/install/{plugin_id}
```

请求体：
```json
{
  "version": "1.0.0"  // 可选，默认为最新版本
}
```

响应：
```json
{
  "success": true,
  "message": "插件安装成功",
  "plugin": {
    "id": "weather",
    "name": "天气查询",
    "version": "1.0.0"
  }
}
```

#### 同步插件仓库

```python
POST /api/plugin_marketplace/sync
```

响应：
```json
{
  "success": true,
  "message": "仓库同步成功",
  "new_plugins": 5,
  "updated_plugins": 3
}
```

## 事件系统

XBotV2提供了一个事件系统，允许插件监听和响应各种事件。插件可以通过实现特定的方法来处理这些事件。

### 消息事件

```python
async def on_message(self, message: dict):
    """
    处理消息事件
    
    参数:
        message (dict): 消息字典，包含以下字段:
            - id: 消息ID
            - type: 消息类型(1=文本, 3=图片, 34=语音, 43=视频, 49=文件/链接等)
            - sender: 发送者wxid
            - content: 消息内容
            - timestamp: 时间戳
            - raw: 原始消息数据
    """
```

### 好友请求事件

```python
async def on_friend_request(self, request: dict):
    """
    处理好友请求事件
    
    参数:
        request (dict): 请求信息，包含字段:
            - v1: v1值
            - v2: v2值
            - content: 验证消息
            - scene: 添加方式
            - nickname: 请求者昵称
    """
```

### 群聊邀请事件

```python
async def on_chatroom_invite(self, invite: dict):
    """
    处理群聊邀请事件
    
    参数:
        invite (dict): 邀请信息，包含字段:
            - chatroom_id: 群聊ID
            - inviter: 邀请者wxid
            - chat_name: 群聊名称
    """
```

### 定时事件

```python
async def on_timer(self, timestamp: int):
    """
    处理定时事件，每分钟触发一次
    
    参数:
        timestamp (int): 当前时间戳
    """
```

### 系统事件

```python
async def on_login(self, info: dict):
    """
    处理登录成功事件
    
    参数:
        info (dict): 登录信息
    """

async def on_logout(self, reason: str):
    """
    处理登出事件
    
    参数:
        reason (str): 登出原因
    """
```

## 最佳实践

### 异步编程

XBotV2使用异步编程模型，所有API调用都应该使用`await`关键字。避免使用阻塞操作，如`time.sleep()`，应该使用`await asyncio.sleep()`代替。

```python
# 错误示例
import time
def some_method(self):
    time.sleep(1)  # 会阻塞整个程序
    
# 正确示例
import asyncio
async def some_method(self):
    await asyncio.sleep(1)  # 不会阻塞
```

### 错误处理

始终对API调用进行错误处理，捕获可能的异常并妥善处理。

```python
try:
    result = await self.bot.send_text_message("wxid_abc123", "你好")
    if not result["success"]:
        logger.error(f"发送失败: {result['error_msg']}")
except Exception as e:
    logger.error(f"发送消息时出错: {e}")
```

### 日志记录

使用`loguru.logger`记录插件的活动和错误，有助于调试和监控。

```python
from loguru import logger

logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误")
```

### 资源管理

妥善管理资源，特别是临时文件和网络连接。

```python
import aiohttp
import os

async def fetch_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
            
# 临时文件使用后删除
def cleanup_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
```

### 插件间通信

如果需要与其他插件通信，建议通过数据库或事件系统进行，避免直接依赖。

```python
# 通过数据库共享数据
shared_db = KeyValDB("shared_data")
await shared_db.set("weather_cache", weather_data)

# 其他插件读取
weather_data = await shared_db.get("weather_cache")
```

## 调试技巧

1. 设置适当的日志级别，以便查看详细信息
2. 使用Web界面的插件管理功能查看错误消息
3. 检查logs目录下的日志文件获取更多信息
4. 禁用其他插件，隔离测试特定插件
5. 使用虚拟测试环境进行插件开发，避免影响生产环境 