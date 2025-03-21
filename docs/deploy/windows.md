# Windows 部署指南

本指南将帮助您在Windows系统上部署XBotV2。

## 系统要求

- Windows 10/11 (64位)
- Python 3.9或更高版本
- 至少2GB可用内存
- 至少500MB可用磁盘空间
- 稳定的网络连接

## 安装步骤

### 1. 安装Python环境

1. 访问[Python官网](https://www.python.org/downloads/)下载最新版本的Python安装包。
2. 运行安装程序，勾选"Add Python to PATH"选项，然后点击"Install Now"。
3. 安装完成后，打开命令提示符(CMD)，输入以下命令验证Python安装：

```bash
python --version
pip --version
```

### 2. 下载XBotV2

1. 访问[XBotV2 GitHub页面](https://github.com/xiaoxinkeji/xbotv2)下载最新版本的源代码。
2. 点击"Code"按钮，然后选择"Download ZIP"。
3. 解压下载的ZIP文件到您选择的目录，例如`C:\XBotV2`。

或者，如果您已安装Git，可以使用以下命令克隆存储库：

```bash
git clone https://github.com/xiaoxinkeji/xbotv2.git C:\XBotV2
```

### 3. 安装依赖

1. 打开命令提示符(CMD)。
2. 导航到XBotV2目录：

```bash
cd C:\XBotV2
```

3. 安装所需的Python依赖包：

```bash
pip install -r requirements.txt
```

### 4. 配置XBotV2

1. 在XBotV2目录中找到`config.example.toml`文件，并将其复制为`config.toml`。
2. 使用文本编辑器（如记事本或VS Code）打开`config.toml`。
3. 配置以下必要参数：
   - `api_server.enable`：设置为`true`
   - `api_server.ip`：通常设置为`127.0.0.1`
   - `api_server.port`：设置API服务器端口（默认为`8000`）
   - `web.enable`：设置为`true`
   - `web.host`：通常设置为`0.0.0.0`
   - `web.port`：设置Web界面端口（默认为`8080`）
   - `bot.admin_wxid`：设置管理员的微信ID
   - 根据需要配置其他选项

### 5. 启动XBotV2

1. 在命令提示符中，确保您仍在XBotV2目录中。
2. 使用以下命令启动XBotV2：

```bash
python main.py
```

3. 首次启动时，系统会自动创建必要的目录和数据库文件。

### 6. 登录微信

1. 启动后，在浏览器中访问：`http://localhost:8080`（或您配置的其他端口）。
2. 在Web界面中，点击"登录"按钮。
3. 使用手机微信扫描二维码完成登录。

### 7. 设置为Windows服务（可选）

为了使XBotV2在后台运行，并在Windows启动时自动启动，您可以将其设置为Windows服务：

1. 安装NSSM（Non-Sucking Service Manager）：
   - 从[NSSM官网](https://nssm.cc/download)下载最新版本
   - 解压并将`nssm.exe`放置在可访问的位置

2. 使用管理员权限打开命令提示符，执行以下命令：

```bash
nssm install XBotV2
```

3. 在打开的配置窗口中：
   - Path：输入Python的完整路径（通常是`C:\Users\username\AppData\Local\Programs\Python\Python39\python.exe`）
   - Startup directory：输入XBotV2的目录（例如`C:\XBotV2`）
   - Arguments：输入`main.py`
   
4. 点击"Install service"按钮。

5. 服务安装后，您可以通过Windows服务管理器启动、停止或配置该服务。

## 常见问题解决

### Python依赖安装失败

如果安装依赖时出现错误，请尝试：

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

如果特定包安装失败，可以尝试单独安装：

```bash
pip install 包名 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 无法启动Web界面

1. 检查配置文件中的`web.enable`是否设置为`true`。
2. 确认端口未被其他应用占用。可以尝试更改`web.port`为其他值，如`8081`。
3. 检查Windows防火墙是否阻止了端口访问。

### 登录失败

1. 确保您的微信版本是最新的。
2. 尝试重启XBotV2并重新登录。
3. 检查您的网络连接是否稳定。

### 服务崩溃或停止

1. 检查日志文件（位于`logs`目录）以识别问题。
2. 确保系统资源（内存、CPU）充足。
3. 如有需要，增加服务的内存限制。

## 升级指南

升级XBotV2到新版本时，请遵循以下步骤：

1. 备份您的`config.toml`和`plugins`目录。
2. 下载最新版本的XBotV2。
3. 替换所有文件，但保留您的备份文件。
4. 还原您的`config.toml`和自定义插件。
5. 重新启动XBotV2。

## 日志文件

XBotV2的日志文件存储在`logs`目录中，格式为`xbot_YYYY-MM-DD.log`。查看这些文件可以帮助您诊断问题。

## 资源优化

为了在Windows上获得更好的性能，建议：

1. 使用SSD存储XBotV2。
2. 确保系统有足够的可用内存（至少2GB）。
3. 定期清理日志文件以节省磁盘空间。
4. 在使用频率较高的情况下，考虑增加系统资源分配。

## 更多帮助

如果您遇到未在此文档中列出的问题，请参考：

- [常见问题解答](/faq)
- [GitHub问题页面](https://github.com/xiaoxinkeji/xbotv2/issues)
- [社区支持论坛](#)（待添加） 