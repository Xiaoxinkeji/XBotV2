# XYBot Web管理界面部署指南

本文档提供了部署XYBot Web管理界面的步骤和建议。

## 系统要求

- Python 3.8+
- 推荐使用Ubuntu 20.04 LTS或更高版本
- 最小配置: 1GB内存, 10GB存储空间
- 推荐配置: 2GB内存, 20GB存储空间

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

或者单独安装所需的包：

```bash
pip install fastapi uvicorn jinja2 sqlalchemy asyncpg psutil redis python-dotenv python-multipart tomli-w
```

### 2. 配置Web管理界面

创建一个`.env`文件在项目根目录：

```
WEB_HOST=127.0.0.1  # 只允许本地访问，设置为0.0.0.0可从任意IP访问
WEB_PORT=8080       # Web服务端口
DEBUG=false         # 调试模式
LOG_LEVEL=info      # 日志级别: debug, info, warning, error
```

### 3. 启动服务

```bash
python -m web_ui.main
```

也可以使用命令行参数覆盖配置:

```bash
python -m web_ui.main --host 0.0.0.0 --port 8080 --debug
```

## 生产环境部署

### 使用Systemd服务(推荐)

1. 创建服务文件 `/etc/systemd/system/xybot-web.service`:

```
[Unit]
Description=XYBot Web Management Interface
After=network.target

[Service]
User=xybot
WorkingDirectory=/path/to/xybot
ExecStart=/path/to/python -m web_ui.main
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

2. 启动服务:

```bash
sudo systemctl enable xybot-web
sudo systemctl start xybot-web
```

3. 查看服务状态:

```bash
sudo systemctl status xybot-web
```

### 使用Docker部署

1. 创建Dockerfile:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "-m", "web_ui.main", "--host", "0.0.0.0"]
```

2. 构建并运行Docker镜像:

```bash
docker build -t xybot-web .
docker run -d -p 8080:8080 --name xybot-web xybot-web
```

## Nginx反向代理配置(推荐)

要通过域名访问并添加HTTPS支持，使用Nginx作为反向代理:

```nginx
server {
    listen 80;
    server_name admin.your-domain.com;
    
    # 重定向到HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name admin.your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 安全建议

1. **更改默认密码**: 首次登录后立即修改默认管理员密码(admin123)
2. **使用HTTPS**: 生产环境中强烈建议使用HTTPS加密通信
3. **限制访问IP**: 通过防火墙限制允许访问的IP地址
4. **定期备份**: 定期备份数据库，保护重要数据
5. **启用日志监控**: 定期检查日志文件，及时发现异常行为

## 故障排除

1. **服务无法启动**: 
   - 检查日志文件`web_ui.log`查看具体错误信息
   - 确保依赖已正确安装
   - 验证端口未被占用(`netstat -tuln | grep 8080`)

2. **无法访问管理界面**:
   - 确认服务已启动(`systemctl status xybot-web`)
   - 检查防火墙是否允许访问该端口
   - 验证主机名和端口配置正确

3. **登录失败**:
   - 默认用户名: `admin` 密码: `admin123`
   - 如忘记密码，可以删除`web_ui/data/admin.json`文件，系统将重新创建默认账户

## 性能优化

1. **增加工作进程**: 在高负载情况下，可以调整Uvicorn工作进程数
2. **数据库索引**: 为常用查询添加适当的数据库索引
3. **静态文件缓存**: 通过Nginx为静态文件设置适当的缓存策略

## 更新与维护

1. 从Git仓库获取最新代码:
```bash
git pull origin main
```

2. 重启服务:
```bash
sudo systemctl restart xybot-web
```

## 常见问题

**Q: 如何重置管理员密码?**  
A: 删除`web_ui/data/admin.json`文件，重启服务后将重置为默认密码。

**Q: 如何更改监听端口?**  
A: 修改.env文件中的WEB_PORT值，或使用--port命令行参数。

**Q: 如何备份数据?**  
A: 定期备份PostgreSQL数据库和`web_ui/data`目录下的文件。 