# Linux 部署指南

本指南将帮助您在Linux系统上部署XBotV2。

## 系统要求

- 任何主流Linux发行版（Ubuntu, Debian, CentOS, Fedora等）
- Python 3.9或更高版本
- 至少1GB可用内存
- 至少500MB可用磁盘空间
- 稳定的网络连接

## 安装步骤

### 1. 安装必要的系统依赖

#### Ubuntu/Debian系统:

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git
```

#### CentOS/RHEL系统:

```bash
sudo yum update
sudo yum install -y python3 python3-pip git
```

#### Fedora系统:

```bash
sudo dnf update
sudo dnf install -y python3 python3-pip git
```

### 2. 下载XBotV2

使用Git克隆XBotV2存储库：

```bash
git clone https://github.com/xiaoxinkeji/xbotv2.git
cd xbotv2
```

或者，如果您没有安装Git，可以下载ZIP文件并解压：

```bash
wget https://github.com/xiaoxinkeji/xbotv2/archive/main.zip
unzip main.zip
cd xbotv2-main
```

### 3. 创建虚拟环境（推荐）

创建并激活Python虚拟环境可以避免依赖冲突：

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. 安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. 配置XBotV2

1. 复制示例配置文件并根据需要修改：

```bash
cp config.example.toml config.toml
```

2. 使用您喜欢的文本编辑器（如nano、vim或gedit）编辑配置文件：

```bash
nano config.toml
```

3. 配置以下必要参数：
   - `api_server.enable`：设置为`true`
   - `api_server.ip`：通常设置为`127.0.0.1`
   - `api_server.port`：设置API服务器端口（默认为`8000`）
   - `web.enable`：设置为`true`
   - `web.host`：通常设置为`0.0.0.0`
   - `web.port`：设置Web界面端口（默认为`8080`）
   - `bot.admin_wxid`：设置管理员的微信ID
   - 根据需要配置其他选项

### 6. 启动XBotV2

```bash
python3 main.py
```

如果使用虚拟环境，请确保已激活：

```bash
source venv/bin/activate
python main.py
```

### 7. 登录微信

1. 在浏览器中访问：`http://YOUR_SERVER_IP:8080`（或您配置的其他端口）。
2. 在Web界面中，点击"登录"按钮。
3. 使用手机微信扫描二维码完成登录。

## 设置为系统服务

为了让XBotV2在后台运行，并在系统启动时自动启动，您可以将其设置为系统服务。

### 使用Systemd（适用于大多数现代Linux发行版）

1. 创建服务文件：

```bash
sudo nano /etc/systemd/system/xbotv2.service
```

2. 添加以下内容（请根据您的实际路径进行调整）：

```ini
[Unit]
Description=XBotV2 WeChat Bot
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/path/to/xbotv2
ExecStart=/path/to/xbotv2/venv/bin/python main.py
Restart=on-failure
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=xbotv2

[Install]
WantedBy=multi-user.target
```

3. 替换`YOUR_USERNAME`为您的Linux用户名，并调整路径。

4. 启用并启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable xbotv2.service
sudo systemctl start xbotv2.service
```

5. 检查服务状态：

```bash
sudo systemctl status xbotv2.service
```

## 防火墙配置

如果您使用防火墙，需要开放Web界面端口：

### UFW（Ubuntu/Debian）:

```bash
sudo ufw allow 8080/tcp
```

### Firewalld（CentOS/RHEL/Fedora）:

```bash
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
```

## 日志管理

XBotV2的日志存储在`logs`目录中。您可以使用标准Linux工具查看日志：

```bash
tail -f logs/xbot_$(date +%Y-%m-%d).log
```

为了防止日志文件占用过多空间，可以设置日志轮换：

1. 安装logrotate（如果尚未安装）：

```bash
sudo apt install logrotate  # Ubuntu/Debian
sudo yum install logrotate  # CentOS/RHEL
sudo dnf install logrotate  # Fedora
```

2. 创建XBotV2的logrotate配置：

```bash
sudo nano /etc/logrotate.d/xbotv2
```

3. 添加以下内容（根据实际路径调整）：

```
/path/to/xbotv2/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 YOUR_USERNAME YOUR_USERNAME
}
```

## 常见问题解决

### 依赖安装失败

如果某些依赖安装失败，可能需要安装额外的系统包：

```bash
# Ubuntu/Debian
sudo apt install -y python3-dev build-essential libssl-dev libffi-dev

# CentOS/RHEL
sudo yum install -y python3-devel gcc openssl-devel bzip2-devel libffi-devel

# Fedora
sudo dnf install -y python3-devel gcc openssl-devel bzip2-devel libffi-devel
```

然后重新安装依赖：

```bash
pip install -r requirements.txt
```

### 无法启动服务

检查服务日志以查找错误原因：

```bash
sudo journalctl -u xbotv2.service
```

### 网络连接问题

1. 确认防火墙设置正确。
2. 验证服务器的IP地址和端口配置。
3. 检查网络连接：

```bash
ping github.com
curl -I http://localhost:8080
```

## 性能优化

### 内存优化

如果您的服务器内存有限，可以考虑添加swap空间：

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 数据库优化

XBotV2使用SQLite数据库。定期维护可以提高性能：

```bash
cd /path/to/xbotv2
sqlite3 data/database.db 'VACUUM;'
```

### 日志管理

定期清理旧日志以节省磁盘空间：

```bash
find /path/to/xbotv2/logs -name "*.log" -type f -mtime +30 -delete
```

## 备份与恢复

定期备份XBotV2的数据：

```bash
# 创建备份目录
mkdir -p ~/xbotv2-backups

# 备份配置和数据
tar -czf ~/xbotv2-backups/xbotv2-backup-$(date +%Y%m%d).tar.gz \
    -C /path/to/xbotv2 config.toml data plugins
```

恢复备份：

```bash
tar -xzf ~/xbotv2-backups/xbotv2-backup-YYYYMMDD.tar.gz -C /path/to/xbotv2
```

## 更新XBotV2

更新XBotV2时，请遵循以下步骤：

```bash
# 停止服务
sudo systemctl stop xbotv2.service

# 备份配置和数据
cp -r config.toml config.toml.bak
cp -r data data.bak
cp -r plugins plugins.bak

# 更新代码
git pull

# 更新依赖
source venv/bin/activate
pip install -r requirements.txt

# 启动服务
sudo systemctl start xbotv2.service
```

## 更多帮助

如果您遇到未在此文档中列出的问题，请参考：

- [常见问题解答](/faq)
- [GitHub问题页面](https://github.com/xiaoxinkeji/xbotv2/issues)
- [社区支持论坛](#)（待添加） 