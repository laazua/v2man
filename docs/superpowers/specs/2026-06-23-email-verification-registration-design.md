# 邮箱验证码注册设计

## 问题

注册接口 `/api/auth/register/` 被限流 `3/hour`，用户频繁遇到 429 Too Many Requests。

## 方案

改为"先注册再激活"流程：注册时创建未激活用户，发送 6 位邮箱验证码，验证后激活账号。

## API 变更

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register/` | 创建用户（is_active=False），自动发送 6 位验证码到邮箱 |
| POST | `/api/auth/activate/` | 提交 email + code，激活账号 |
| POST | `/api/auth/verification-code/resend/` | 重新发送验证码 |

## 限流策略

- 移除注册限流 `RegisterThrottle`（`register` scope）
- 新增 `VerificationCodeThrottle`：验证码发送 `1/minute`
- 全局 `AnonRateThrottle` 仍生效（`20/hour`），兜底保护

## 验证码

- 6 位随机数字
- 存储于缓存（`LocMemCache`），key: `verify_code_{email}`
- 有效期 5 分钟
- 重新发送会覆盖旧验证码并重置 TTL

## 涉及文件

| 文件 | 修改 |
|------|------|
| `app/users/throttles.py` | 新增 `VerificationCodeThrottle`，移除 `RegisterThrottle` |
| `app/users/serializers.py` | 新增 `ActivateSerializer`（email + code） |
| `app/users/views.py` | 修改 `RegisterView.create()` 发验证码，新增 `ActivateView`、`ResendCodeView` |
| `app/users/urls.py` | 新增 activate/、verification-code/resend/ 路由 |
| `app/config/settings.py` | 更新 throttle rates |
| `web/src/api/index.ts` | 新增 activate、resendCode 接口 |
| `web/src/views/Register.vue` | 注册成功后跳转验证码输入页 |

## 数据流

```
POST /register → 创建用户(is_active=False) → 生成 6 位码 → 存缓存(5min) → 发邮件
POST /activate → 校验缓存中 code → is_active=True → 删除缓存 → 返回 Token
POST /resend → 生成新码 → 覆盖缓存 → 发邮件
```

## 未激活用户行为

- 登录时返回 `401 "账号未激活，请先验证邮箱"`
