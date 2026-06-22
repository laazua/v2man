# 容器部署

使用 Docker Compose 一键部署 v2man 管理系统。

---

## 环境要求

| 组件 | 版本要求 |
|------|----------|
| Docker | >= 24.0 |
| Docker Compose | >= 2.20 |

---

## 目录结构

```
v2man/
├── Dockerfile              # 后端 Django 镜像
├── Dockerfile.cron         # 调度器镜像（APScheduler）
├── docker-compose.yml      # 主编排文件
├── nginx.conf              # Nginx 配置
├── app/
│   ├── .env                # 环境变量
│   ├── .env.production     # 生产环境变量（可选）
│   └── ...
└── web/
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

容器部署需要先在前端构建静态文件，因为 Nginx 容器通过挂载卷读取构建产物：

```bash
cd web
npm install
npm run build
cd ..
```

构建产物在 `web/dist/` 目录。

---

## 3. 启动服务

```bash
docker compose up -d
```

启动后包含 4 个容器：

| 容器 | 作用 | 端口 |
|------|------|------|
| `web` | Django + gunicorn 后端 | :8000（内部） |
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

# 创建管理员
docker compose exec web uv run manage.py createsuperuser

# 创建 media 目录
docker compose exec web mkdir -p /app/media
```

---

## 4. 更新部署

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
npm run build
cd ..

# 重建 nginx 容器（加载新构建产物）
docker compose restart nginx
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

## 5. Nginx 配置

`nginx.conf` 已默认配置好：

```nginx
server {
    listen 80;
    server_name _;

    location /api/ {
        proxy_pass http://web:8055;     # 指向 Django 后端容器
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /admin/ {
        proxy_pass http://web:8055;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static/ {
        alias /app/staticfiles/;
    }

    location / {
        root /app/web/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

如需配置 SSL 证书，在 `nginx.conf` 中添加 443 端口的 SSL 配置：

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
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - static:/app/staticfiles:ro
      - dist:/app/web/dist:ro
      - /path/to/ssl:/etc/nginx/ssl:ro      # 挂载 SSL 证书
```

---

## 6. 生产环境 checklist

- [ ] `SECRET_KEY` 已替换为随机字符串（可用 `openssl rand -hex 32` 生成）
- [ ] `DEBUG=False`
- [ ] `ALLOWED_HOSTS` 已设置为实际域名
- [ ] `CORS_ALLOWED_ORIGINS` 已设置为前端域名
- [ ] 数据库使用 PostgreSQL
- [ ] 已配置 SMTP 邮箱（密码重置功能）
- [ ] Nginx 已配置 HTTPS
- [ ] 已执行 `docker compose exec web uv run manage.py migrate`

---

## 7. 常用运维命令

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
