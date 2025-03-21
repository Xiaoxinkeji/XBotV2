# Docker部署指南

Docker是部署XBotV2最简单和推荐的方式，它可以帮助您避免环境配置问题，并且可以在几分钟内完成部署。

## 准备工作

1. 安装Docker和Docker Compose
   - Windows/macOS: 安装[Docker Desktop](https://www.docker.com/products/docker-desktop)
   - Linux: 安装[Docker Engine](https://docs.docker.com/engine/install/)和[Docker Compose](https://docs.docker.com/compose/install/)

2. 确保您的系统满足以下要求：
   - 至少2GB内存
   - 至少10GB磁盘空间
   - 网络连接正常

## 部署步骤

### 1. 下载项目

```bash
git clone https://github.com/xiaoxinkeji/xbotv2.git
cd xbotv2
```

如果您不熟悉Git，也可以从GitHub下载ZIP文件并解压。

### 2. 配置docker-compose.yml

项目根目录已经包含了预配置的`docker-compose.yml`文件，内容如下：

```yaml
version: '3'
services:
  xbotv2:
    build: .
    image: xiaoxinkeji/xbotv2:latest
    container_name: xbotv2
    restart: unless-stopped
    ports:
      - "8080:8080"  # Web界面端口
      - "9000:9000"  # WechatAPI服务器端口
    volumes:
      - ./database:/app/database  # 数据库持久化
      - ./plugins:/app/plugins    # 插件持久化
      - ./resource:/app/resource  # 资源文件持久化
      - ./logs:/app/logs          # 日志持久化
      - ./main_config.toml:/app/main_config.toml  # 主配置文件
    environment:
      - TZ=Asia/Shanghai  # 时区设置
```

您可以根据需要修改端口映射和环境变量。

### 3. 启动容器

在项目根目录下执行：

```bash
docker-compose up -d
```

首次启动会构建镜像，这可能需要几分钟时间。

### 4. 验证部署

启动完成后，可以通过以下方式验证部署是否成功：

1. 访问Web界面: [http://localhost:8080](http://localhost:8080)
2. 默认用户名和密码: admin/admin123

### 5. 查看日志

如果您需要查看日志，可以使用以下命令：

```bash
# 查看容器日志
docker logs xbotv2

# 实时查看日志
docker logs -f xbotv2
```

也可以直接查看logs目录下的日志文件。

## 常见问题

### 端口冲突

如果您的系统中已经有程序占用了8080或9000端口，您可以在`docker-compose.yml`文件中修改端口映射：

```yaml
ports:
  - "8081:8080"  # 将8080端口映射到宿主机的8081端口
  - "9001:9000"  # 将9000端口映射到宿主机的9001端口
```

### 容器无法启动

检查Docker日志以获取更多信息：

```bash
docker logs xbotv2
```

可能的问题包括：
- 磁盘空间不足
- 权限问题
- 配置文件格式错误

### 数据持久化

默认情况下，所有数据都会通过卷映射保存在宿主机上。如果您需要备份数据，只需复制对应的目录即可。

## 更新XBotV2

要更新到最新版本，请执行以下步骤：

```bash
# 进入项目目录
cd xbotv2

# 拉取最新代码
git pull

# 重新构建并启动容器
docker-compose up -d --build
```

## 高级配置

### 使用外部Redis

如果您想使用外部Redis服务器，可以修改`main_config.toml`文件：

```toml
[WechatAPIServer]
redis-host = "your-redis-host"
redis-port = 6379
redis-password = "your-redis-password"
redis-db = 0
```

### Docker网络配置

如果您需要将XBotV2与其他Docker容器连接，可以配置网络：

```yaml
version: '3'
networks:
  app-network:
    driver: bridge

services:
  xbotv2:
    # ... 其他配置 ...
    networks:
      - app-network
  
  redis:
    image: redis:latest
    networks:
      - app-network
```

这样XBotV2可以通过容器名称访问Redis服务。 