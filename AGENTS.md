# AGENTS.md

## 项目目标

v2ray 节点管理系统。功能：
- 管理 v2ray 服务节点
- 生成订阅链接供用户导入
- 统计用户流量使用情况
- 套餐方案：¥2/月、¥5/月、¥10/月

## 项目结构

```
v2man/
├── app/                    # 后端 Django 项目
│   ├── config/             # settings, urls, wsgi
│   ├── users/              # 用户 + JWT 认证 + 钱包/充值
│   ├── nodes/              # v2ray 节点 + 订阅生成 + SSH 同步工具
│   ├── ssh_utils.py    # SSH 直连节点执行配置同步（零依赖系统 ssh 命令）
│   ├── plans/              # 套餐方案
│   ├── traffic/            # 流量日志
│   ├── manage.py
│   └── pyproject.toml      # uv 管理
├── web/                    # 前端 Vue 3 + Vite
│   ├── src/
│   │   ├── views/          # Login, Register, Dashboard, Nodes, Plans, Recharge
│   │   ├── api/            # Axios 封装（自动刷新 JWT）
│   │   ├── router/         # 路由（auth guard）
│   │   ├── types/          # TypeScript 类型
│   └── package.json        # volta + npm
├── Dockerfile              # 生产部署
├── docker-compose.yml      # Django + PostgreSQL
├── nginx.conf              # Nginx 静态文件 + 反向代理
└── AGENTS.md
```

## 代码标准

- 后端：Python 3.13+, uv 管理依赖, Django + DRF + Django ORM
- 前端：Node 24.16+, volta 管理版本, TypeScript, Vue 3 + Vite
- DB：SQLite（开发）/ PostgreSQL（生产）
- 认证：JWT (djangorestframework-simplejwt)
- 整个会话过程用中文交流
- 每次回答问题时加上 `[主人]` 前缀

## 开发者命令

```bash
# 后端
cd app
uv run manage.py runserver              # 启动开发服务器 (:8000)
uv run manage.py makemigrations         # 生成迁移
uv run manage.py migrate                # 执行迁移
uv run manage.py createsuperuser        # 创建管理员
uv run manage.py check_expired          # 检查到期用户并停用

# 前端
cd web
npm run dev                             # 启动 Vite 开发服务器 (:5173)
npm run build                           # 构建生产版本
```

## API 端点

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/auth/login/` | JWT 登录 |
| POST | `/api/auth/refresh/` | 刷新 Token |
| POST | `/api/auth/register/` | 注册（自动创建钱包 + 订阅） |
| GET | `/api/auth/profile/` | 当前用户信息（含余额、订阅token） |
| POST | `/api/auth/recharge/` | 提交充值申请 |
| GET | `/api/plans/` | 套餐列表（公开） |
| POST | `/api/plans/purchase/<id>/` | 扣余额购买套餐 |
| GET | `/api/nodes/` | 节点列表（公开） |
| GET | `/api/subscription/<token>/` | 订阅链接 (Base64 V2Ray) |
| GET | `/api/subscription/<token>/clashmeta/` | Clash 格式 |
| GET | `/api/subscription/<token>/singbox/` | Sing-box 格式 |
| POST | `/api/traffic/record/` | 管理员录入流量 |
| GET | `/api/traffic/stats/` | 用户流量明细（按日汇总） |
| GET | `/admin/` | Django Admin |

## 核心业务流程

1. **注册** → 自动创建 Wallet + Subscription
2. **充值** → 用户提交申请 → 管理员在 Admin 确认到账 → 余额增加
3. **购买套餐** → 选择套餐 → 扣余额 → 更新 plan/traffic/expire 字段
4. **订阅** → 用户从面板复制订阅链接 → 导入 V2Ray/Clash/Sing-box 客户端
5. **流量** → 管理员手动录入 → 自动累加到用户 traffic_used

## 已知注意事项

- `format` 是 DRF 保留关键字，URL kwargs 中需使用 `output_fmt` 替代
- 因网络环境原因，"clash" 关键词在 query 参数中可能被拦截，订阅格式用路径区分而非参数
- 注册信号在 `users/signals.py` 中自动创建钱包
- 管理后台确认充值操作在 UserAdmin 的 `confirm_recharge` action 中
