# v2man 生产化设计

## 业务流程

注册 → 充值（扫码支付宝）→ 管理员确认到账 → 余额增加 → 选择套餐 → 扣余额购买 → 套餐生效 → 订阅链接可用

## 模块 1：生产环境基础

- `settings.py` 改为环境变量驱动（`SECRET_KEY`、`DEBUG`、`DATABASE_URL`、`ALLOWED_HOSTS`）
- 使用 `python-dotenv` 加载 `.env`
- PostgreSQL 配置就绪
- `.env.example` 模板

## 模块 2：钱包 + 充值

- `Wallet` 模型：user（OneToOneField）、balance（BigIntegerField，单位分）
- `Recharge` 模型：user、amount、status（pending/completed）、remark、created_at（auto）、confirmed_at
- 管理后台可确认充值（pending→completed，自动增加 Wallet.balance）
- 前端充值页：展示固定支付宝收款码 + 输入金额 + 提交待审核

## 模块 3：套餐自助购买

- `GET /api/plans/` — 列出可用套餐
- `POST /api/plans/purchase/<id>/` — 扣余额购买
  - 校验余额是否充足
  - 扣除余额
  - 更新 User.plan / traffic_total / expire_date
  - 创建或更新 Subscription
  - 返回订单结果

## 模块 4：流量管理

- `POST /api/traffic/record/` — 管理员录入流量（user_id, upload_bytes, download_bytes, node_name）
- `GET /api/traffic/stats/` — 用户查询自己按日汇总的流量明细
- 录入时自动累加 `User.traffic_used`

## 模块 5：订阅自动创建

- `@receiver(post_save, User)` — 用户注册后自动创建 Subscription（token 即 uuid）
- `GET /api/subscription/<token>/` 支持 ?format=base64|clash|singbox（已实现）

## 模块 6：前端页面完善

- `/register` — 注册页面
- `/recharge` — 充值页面（支付宝码 + 金额输入）
- `/plans` — 套餐选购页面
- 仪表盘升级：余额、订阅链接复制、简单流量图表
- 节点页升级：三种格式链接一键复制

## 模块 7：管理命令

- `python manage.py check_expired` — 检查到期用户，过期自动停用
- `python manage.py reset_traffic` — 月流量重置

## 模块 8：部署配置

- Dockerfile + docker-compose（Django + PostgreSQL + Nginx）
- Gunicorn 配置
- Nginx 静态文件服务
