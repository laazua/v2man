# 源码部署

在裸金属或云服务器上直接部署 v2man 管理系统。

---

## 环境要求

| 组件 | 版本要求 |
|------|----------|
| Python | >= 3.13 |
| Node.js | >= 24.16 |
| npm | 由 volta 自动管理 |
| Database | SQLite（开发）或 PostgreSQL >= 16（生产） |
| uv | 推荐，用于 Python 依赖管理 |

---

## 1. 克隆代码

```bash
git clone <your-repo-url> /opt/v2man
cd /opt/v2man
```

---

## 2. 后端部署

### 2.1 配置环境变量

```bash
cp app/.env.example app/.env
```

编辑 `app/.env`，关键配置项：

```ini
# 安全密钥（生产环境必须更换）
SECRET_KEY=your-very-long-random-secret-key

# 生产关闭 DEBUG
DEBUG=False

# 数据库（默认 SQLite，生产推荐 PostgreSQL）
DATABASE_URL=postgres://user:password@localhost:5432/v2man

# 允许访问的域名（逗号分隔）
ALLOWED_HOSTS=v2man.example.com

# CORS 跨域
CORS_ALLOWED_ORIGINS=https://v2man.example.com

# 静态文件目录
STATIC_ROOT=/opt/v2man/app/staticfiles

# JWT 过期时间
JWT_ACCESS_MINUTES=60
JWT_REFRESH_DAYS=30

# 邮箱配置（密码重置用）
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.qq.com
EMAIL_PORT=465
EMAIL_HOST_USER=noreply@example.com
EMAIL_HOST_PASSWORD=your-smtp-auth-code
EMAIL_USE_SSL=True
DEFAULT_FROM_EMAIL=noreply@example.com
```

### 2.2 安装依赖

```bash
cd app
uv sync
```

### 2.3 初始化数据库

```bash
uv run manage.py migrate
uv run manage.py ensureadmin          # 自动创建默认管理员 admin/admin123
# 或手动创建：uv run manage.py createsuperuser
```

### 2.4 收集静态文件

```bash
uv run manage.py collectstatic --noinput
```

### 2.5 创建 media 目录

```bash
mkdir -p media
```

### 2.6 启动后端服务

开发环境：

```bash
uv run manage.py runserver 0.0.0.0:8055
```

生产环境（推荐 gunicorn + systemd）：

```bash
# 安装 gunicorn（已包含在依赖中）
uv run gunicorn config.wsgi:application --bind 0.0.0.0:8055 --workers 4
```

---

## 3. 前端部署

### 3.1 安装依赖

```bash
cd web
npm install
```

### 3.2 构建生产版本

```bash
npm run build
```

构建产物在 `web/dist/` 目录，可直接用 Nginx 托管。

### 3.3 开发模式（配合后端代理）

```bash
npm run dev
```

默认监听 `0.0.0.0:5173`，API 请求通过 Vite proxy 转发到 `127.0.0.1:8055`。

---

## 4. Nginx 配置

将 `nginx.conf` 中的 `proxy_pass` 地址改为后端实际地址，`root` 指向前端构建目录：

```nginx
server {
    listen 80;
    server_name v2man.example.com;

    location /api/ {
        proxy_pass http://127.0.0.1:8055;       # Django 后端
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /admin/ {
        proxy_pass http://127.0.0.1:8055;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /opt/v2man/app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /opt/v2man/app/media/;
    }

    location / {
        root /opt/v2man/web/dist;
        try_files $uri $uri/ /index.html;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## 5. 启动调度器

后台调度器负责定时采集节点流量和同步用户配置：

```bash
cd app
uv run manage.py run_scheduler
```

建议将其托管为 systemd 服务：

```ini
# /etc/systemd/system/v2man-scheduler.service
[Unit]
Description=v2man scheduler
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/v2man/app
ExecStart=/root/.local/bin/uv run manage.py run_scheduler
Restart=always
User=root

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now v2man-scheduler
```

---

## 6. systemd 完整配置示例

### Django 后端

```ini
# /etc/systemd/system/v2man-web.service
[Unit]
Description=v2man Django backend
After=network.target postgresql.service

[Service]
Type=simple
WorkingDirectory=/opt/v2man/app
ExecStart=/root/.local/bin/uv run gunicorn config.wsgi:application --bind 127.0.0.1:8055 --workers 4
Restart=always
User=root

[Install]
WantedBy=multi-user.target
```

---

## 7. 防火墙

```bash
# Nginx 暴露 80/443
ufw allow 80/tcp
ufw allow 443/tcp
```
