# 容器部署

使用 Docker Compose 一键部署 v2man 管理系统。

---

## 环境要求

| 组件 | 版本要求 |
|------|----------|
| Docker | >= 24.0 |
| Docker Compose | >= 2.20 |
| Node.js | >= 22（构建前端用） |

---

## 目录结构

```
v2man/
├── Dockerfile              # 后端 Django 镜像
├── Dockerfile.cron         # 调度器镜像（APScheduler）
├── Dockerfile.nginx        # Nginx 镜像（仅打包，不构建）
├── docker-compose.yml      # 主编排文件
├── nginx.conf              # Nginx 配置
├── app/
│   ├── .env                # 环境变量
│   ├── .env.production     # 生产环境变量（可选）
│   └── ...
└── web/
    ├── dist/               # 前端构建产物（需本地构建）
    └── ...
```

---

## 1. 配置环境变量

```bash
cp app/.env.example app/.env
```

编辑 `app/.env`，生产环境建议：

```ini
SECRET_KEY=your-very-long-random-secret-key
DEBUG=False
DATABASE_URL=postgres://v2man:v2man@db:5432/v2man
ALLOWED_HOSTS=v2man.example.com
CORS_ALLOWED_ORIGINS=https://v2man.example.com
STATIC_ROOT=/app/staticfiles

JWT_ACCESS_MINUTES=60
JWT_REFRESH_DAYS=30

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.qq.com
EMAIL_PORT=465
EMAIL_HOST_USER=noreply@example.com
EMAIL_HOST_PASSWORD=your-smtp-auth-code
EMAIL_USE_SSL=True
DEFAULT_FROM_EMAIL=noreply@example.com
```

### 数据库连接说明

`docker-compose.yml` 中的数据库账号密码默认值：

```
POSTGRES_DB=v2man
POSTGRES_USER=v2man
POSTGRES_PASSWORD=v2man
```

如果修改了这些值，`DATABASE_URL` 中的用户名密码也要同步修改。

### 生产专属配置（可选）

创建 `app/.env.production`，其中的变量会覆盖 `.env` 中的同名变量（适合将密钥等敏感信息单独存放）：

```ini
# 此文件中的变量优先级高于 .env
SECRET_KEY=production-only-secret
```

---

## 2. 构建前端

Nginx 镜像通过 `COPY web/dist` 将前端产物打包进镜像，因此需要在构建 Docker 镜像前先本地构建前端：

```bash
cd web
npm install
npm run build-only
cd ..
```

构建产物在 `web/dist/` 目录。

> 注意：使用 `build-only` 脚本（仅 `vite build`），跳过 `vue-tsc` 类型检查。生产容器构建不依赖 type-check，后者应在 CI 或开发阶段完成。

---

## 3. 构建镜像

```bash
docker compose build
```

### 按需构建单个服务

```bash
docker compose build web      # 仅后端
docker compose build cron     # 仅调度器
docker compose build nginx    # 仅 Nginx（需先构建前端）
```

---

## 4. 启动服务

```bash
docker compose up -d
```

启动后包含 4 个容器：

| 容器 | 作用 | 端口 |
|------|------|------|
| `web` | Django + gunicorn 后端 | :8055（外部） |
| `nginx` | 反向代理 + 静态文件 | :80（外部） |
| `cron` | APScheduler 调度器 | - |
| `db` | PostgreSQL 数据库 | :5432（内部） |

### 查看启动日志

```bash
docker compose logs -f
```

### 初始化数据库

```bash
# 执行数据库迁移
docker compose exec web uv run manage.py migrate

# 创建管理员（容器启动时自动创建，也可手动执行）
docker compose exec web uv run manage.py ensureadmin

# 创建 media 目录
docker compose exec web mkdir -p /app/media
```

> **自动创建管理员**：容器首次启动时，`Dockerfile` 中的启动链会自动执行 `manage.py ensureadmin`，
> 创建默认管理员账号 `admin / admin123`（邮箱 `admin@v2man.local`）。
> 如需自定义用户名或密码，可手动执行：
> ```bash
> docker compose exec web uv run manage.py ensureadmin --username myadmin --password mypass
> ```
> 如果系统中已有 superuser，该命令会直接跳过，不会覆盖已有账号。

---

## 5. 更新部署

### 更新后端代码

```bash
git pull

# 重建后端和调度器镜像
docker compose build web cron

# 重启服务
docker compose up -d
```

### 更新前端代码

```bash
cd web
npm install
npm run build-only
cd ..

# 重建 nginx 镜像（打包新构建产物）
docker compose build nginx

# 重启
docker compose up -d
```

### 快速重启所有服务

```bash
docker compose down
docker compose up -d
```

### 查看调度器日志

```bash
docker compose logs -f cron
```

---

## 6. Nginx HTTPS 配置

`nginx.conf` 已默认配置 HTTP 反向代理。如需启用 HTTPS，在 `nginx.conf` 中添加：

```nginx
server {
    listen 443 ssl;
    server_name v2man.example.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    # ... 同上 location 配置
}

server {
    listen 80;
    server_name v2man.example.com;
    return 301 https://$host$request_uri;
}
```

然后在 `docker-compose.yml` 的 nginx 服务中添加 SSL 证书挂载：

```yaml
services:
  nginx:
    volumes:
      - static:/app/staticfiles:ro
      - /path/to/ssl:/etc/nginx/ssl:ro
```

---

## 7. 生产环境 checklist

- [ ] `SECRET_KEY` 已替换为随机字符串（可用 `openssl rand -hex 32` 生成）
- [ ] `DEBUG=False`
- [ ] `ALLOWED_HOSTS` 已设置为实际域名
- [ ] `CORS_ALLOWED_ORIGINS` 已设置为前端域名
- [ ] 数据库使用 PostgreSQL
- [ ] 已配置 SMTP 邮箱（密码重置功能）
- [ ] Nginx 已配置 HTTPS
- [ ] 容器启动后自动执行 `migrate` + `ensureadmin`，无需手动操作

---

## 8. 常用运维命令

```bash
# 进入 Django shell
docker compose exec web uv run manage.py shell

# 手动采集节点流量
docker compose exec web uv run manage.py collect_traffic

# 手动同步用户到节点
docker compose exec web uv run manage.py sync_users

# 手动检查到期用户
docker compose exec web uv run manage.py check_expired

# 备份数据库
docker compose exec db pg_dump -U v2man v2man > backup.sql

# 查看容器资源占用
docker compose stats
```
