# 系统配置说明

XBotV2使用TOML格式的配置文件来管理系统设置。本文档详细说明了配置文件的各个部分及其含义，帮助您根据实际需求自定义XBotV2。

## 配置文件位置

配置文件位于XBotV2根目录下，名为`config.toml`。首次安装时，您需要将`config.example.toml`复制为`config.toml`并进行修改。

## 配置文件结构

配置文件主要分为以下几个部分：

1. API服务器配置
2. 机器人核心配置
3. Web界面配置
4. 日志配置
5. 消息过滤器配置
6. 插件配置

以下是每个部分的详细说明。

## API服务器配置

```toml
[api_server]
enable = true
ip = "127.0.0.1"
port = 8000
log_level = "INFO"
```

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| enable | 布尔值 | 是否启用API服务器 | true |
| ip | 字符串 | API服务器绑定的IP地址 | "127.0.0.1" |
| port | 整数 | API服务器监听的端口 | 8000 |
| log_level | 字符串 | 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL） | "INFO" |

## 机器人核心配置

```toml
[bot]
admin_wxid = "wxid_yourwxid"
admin_nickname = "Your Name"
nickname = "XBot"
check_interval = 0.5
command_prefix = "/"
plugin_dir = "plugins"
data_dir = "data"
auto_login = true
qrcode_timeout = 300
```

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| admin_wxid | 字符串 | 管理员的微信ID | "" |
| admin_nickname | 字符串 | 管理员的昵称 | "" |
| nickname | 字符串 | 机器人的昵称 | "XBot" |
| check_interval | 浮点数 | 消息检查间隔（秒） | 0.5 |
| command_prefix | 字符串 | 命令前缀 | "/" |
| plugin_dir | 字符串 | 插件目录 | "plugins" |
| data_dir | 字符串 | 数据目录 | "data" |
| auto_login | 布尔值 | 启动时是否自动登录 | true |
| qrcode_timeout | 整数 | 二维码超时时间（秒） | 300 |

## Web界面配置

```toml
[web]
enable = true
host = "0.0.0.0"
port = 8080
debug = false
secret_key = "your_secret_key_here"
session_cookie = "xbot_session"
session_lifetime = 86400
templates_dir = "web/templates"
static_dir = "web/static"
```

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| enable | 布尔值 | 是否启用Web界面 | true |
| host | 字符串 | Web服务器绑定的IP地址 | "0.0.0.0" |
| port | 整数 | Web服务器监听的端口 | 8080 |
| debug | 布尔值 | 是否启用调试模式 | false |
| secret_key | 字符串 | 用于会话加密的密钥 | 随机生成 |
| session_cookie | 字符串 | 会话Cookie名称 | "xbot_session" |
| session_lifetime | 整数 | 会话生存时间（秒） | 86400 |
| templates_dir | 字符串 | 模板目录 | "web/templates" |
| static_dir | 字符串 | 静态文件目录 | "web/static" |

## 日志配置

```toml
[logging]
level = "INFO"
format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
log_file = "logs/xbot_{time:YYYY-MM-DD}.log"
rotation = "00:00"
retention = "7 days"
compression = "zip"
```

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| level | 字符串 | 日志级别 | "INFO" |
| format | 字符串 | 日志格式 | 见上 |
| log_file | 字符串 | 日志文件路径（支持日期格式化） | "logs/xbot_{time:YYYY-MM-DD}.log" |
| rotation | 字符串 | 日志轮换时间 | "00:00" |
| retention | 字符串 | 日志保留时间 | "7 days" |
| compression | 字符串 | 日志压缩格式 | "zip" |

## 消息过滤器配置

```toml
[message_filter]
enable = true
block_self = true
block_official_account = true
block_group_message = false
allowed_groups = []
blocked_users = []
```

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| enable | 布尔值 | 是否启用消息过滤 | true |
| block_self | 布尔值 | 是否过滤自己发送的消息 | true |
| block_official_account | 布尔值 | 是否过滤公众号消息 | true |
| block_group_message | 布尔值 | 是否过滤群聊消息 | false |
| allowed_groups | 字符串数组 | 允许的群聊ID列表 | [] |
| blocked_users | 字符串数组 | 阻止的用户ID列表 | [] |

## 数据库配置

```toml
[database]
type = "sqlite"
path = "data/database.db"
```

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| type | 字符串 | 数据库类型 | "sqlite" |
| path | 字符串 | 数据库文件路径 | "data/database.db" |

## 插件市场配置

```toml
[plugin_market]
enable = true
repository_url = "https://raw.githubusercontent.com/username/xbotv2-plugins/main/repository.json"
cache_time = 3600
```

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| enable | 布尔值 | 是否启用插件市场 | true |
| repository_url | 字符串 | 插件仓库URL | 见上 |
| cache_time | 整数 | 仓库缓存时间（秒） | 3600 |

## 插件配置

每个插件可以有自己的配置部分，格式如下：

```toml
[plugins.plugin_name]
enable = true
# 插件特定配置...
```

例如，对于一个名为"weather"的插件：

```toml
[plugins.weather]
enable = true
api_key = "your_api_key_here"
default_city = "Beijing"
```

## 示例完整配置

以下是一个完整的配置文件示例：

```toml
[api_server]
enable = true
ip = "127.0.0.1"
port = 8000
log_level = "INFO"

[bot]
admin_wxid = "wxid_abcdefg"
admin_nickname = "Admin"
nickname = "XBot"
check_interval = 0.5
command_prefix = "/"
plugin_dir = "plugins"
data_dir = "data"
auto_login = true
qrcode_timeout = 300

[web]
enable = true
host = "0.0.0.0"
port = 8080
debug = false
secret_key = "some_random_secret_key"
session_cookie = "xbot_session"
session_lifetime = 86400
templates_dir = "web/templates"
static_dir = "web/static"

[logging]
level = "INFO"
format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
log_file = "logs/xbot_{time:YYYY-MM-DD}.log"
rotation = "00:00"
retention = "7 days"
compression = "zip"

[message_filter]
enable = true
block_self = true
block_official_account = true
block_group_message = false
allowed_groups = ["group1", "group2"]
blocked_users = ["user1", "user2"]

[database]
type = "sqlite"
path = "data/database.db"

[plugin_market]
enable = true
repository_url = "https://raw.githubusercontent.com/username/xbotv2-plugins/main/repository.json"
cache_time = 3600

[plugins.ai_chat]
enable = true
api_key = "your_api_key_here"
model = "deepseek-chat"
temperature = 0.7

[plugins.weather]
enable = true
api_key = "your_weather_api_key"
default_city = "Beijing"

[plugins.news]
enable = true
update_interval = 3600
sources = ["source1", "source2"]
```

## 配置最佳实践

1. **安全性**：
   - 不要使用默认的`secret_key`，应该设置为一个随机字符串。
   - 对于生产环境，将`web.host`设置为内部IP或"127.0.0.1"，并使用反向代理（如Nginx）提供外部访问。
   - 保护好`admin_wxid`，这是具有完全管理权限的账号。

2. **性能调优**：
   - `check_interval`影响消息响应速度和CPU使用率，可根据需要调整。
   - 对于高并发场景，考虑增加`web`部分的配置项，如增加工作进程数。

3. **网络配置**：
   - 如果在局域网中部署，将`web.host`设置为"0.0.0.0"使其在所有网络接口上可访问。
   - 对于公网部署，请确保正确配置防火墙，只开放必要的端口。

4. **插件管理**：
   - 禁用不需要的插件可以减少资源占用。
   - 定期更新插件仓库以获取最新功能和安全修复。

## 配置文件的热重载

XBotV2支持配置热重载，可以在不重启系统的情况下应用配置更改。在Web界面的"系统设置"页面中，可以修改配置并应用更改。

也可以通过API或命令行方式触发配置重载：

```bash
# 通过API重载配置
curl -X POST http://localhost:8000/api/system/reload_config

# 通过命令行重载配置（在XBotV2管理界面中）
/reload_config
```

注意：某些配置更改（如更改端口或主机绑定）仍然需要重启服务才能生效。

## 高级配置

### 使用环境变量

XBotV2支持通过环境变量覆盖配置文件中的设置，格式为`XBOT_SECTION_KEY`。例如：

- `XBOT_WEB_PORT=8081`会覆盖`[web]`部分的`port`值
- `XBOT_BOT_ADMIN_WXID=wxid_new`会覆盖`[bot]`部分的`admin_wxid`值

这对于Docker部署和CI/CD环境特别有用。

### 配置文件路径

默认情况下，XBotV2在当前目录查找`config.toml`。可以通过环境变量或命令行参数指定不同的配置文件：

```bash
# 使用环境变量
export XBOT_CONFIG_PATH=/path/to/my/config.toml
python main.py

# 使用命令行参数
python main.py --config /path/to/my/config.toml
```

## 故障排除

如果您在配置XBotV2时遇到问题，请检查：

1. 配置文件语法是否正确（TOML格式要求严格）
2. 路径是否正确设置（相对路径基于XBotV2的根目录）
3. 端口是否被其他应用占用
4. 检查日志文件中的错误信息

常见错误：

- `SyntaxError`: TOML语法错误，检查配置文件格式
- `PermissionError`: 文件或目录权限问题
- `ConnectionRefusedError`: 端口可能被占用或防火墙阻止

## 配置备份

建议定期备份您的配置文件，特别是在进行重大更改之前：

```bash
# 在更改前备份配置
cp config.toml config.toml.bak

# 或者创建带时间戳的备份
cp config.toml config.toml.$(date +%Y%m%d)
``` 