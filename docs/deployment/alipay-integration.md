# 对接真实支付宝

当前系统已内置支付宝当面付驱动，只需修改后台配置即可切换到真实支付宝支付。

---

## 前提条件

1. 企业或个体工商户的支付宝账号
2. 在 [支付宝开放平台](https://open.alipay.com) 注册开发者账号并创建应用
3. 完成应用的签约（"当面付"产品）

---

## 申请步骤

### 1. 创建应用

登录 [支付宝开放平台](https://open.alipay.com) → 控制台 → 网页/移动应用 → 创建应用。

应用类型选择 **「当面付」**，创建完成后提交审核。

### 2. 配置密钥

在应用的 **「开发设置」** 中：

1. **接口加签方式** → 选择 **「公钥模式」** → 设置 **「RSA2」** 签名
2. 使用支付宝官方工具生成应用私钥和公钥
3. 上传应用公钥 → 获取支付宝公钥

### 3. 配置回调地址

在 **「开发设置」** → **「消息接收地址」** 中，填写：

```
https://你的域名/api/auth/payment/notify/
```

这是支付宝支付成功后异步通知的接收地址。

### 4. 签约产品

在应用的 **「产品绑定」** 中，添加 **「当面付」** 产品并提交签约。

---

## 系统配置

### 1. 安装支付宝 SDK

```bash
cd app
uv add alipay-sdk-python
```

### 2. 配置管理后台

登录管理后台 → **管理功能** → **充值设置**：

1. **充值模式** → 切换到 **「自动到账模式」**
2. **支付驱动** → 切换到 **「支付宝当面付（生产用）」**
3. 填入以下从支付宝开放平台获取的信息：

| 配置项 | 说明 |
|--------|------|
| **应用 APPID** | 支付宝应用的 APPID，如 `2021003126698765` |
| **应用私钥** | 生成的应用私钥，PEM 格式，含 `-----BEGIN RSA PRIVATE KEY-----` |
| **支付宝公钥** | 支付宝开放平台提供的公钥，PEM 格式，含 `-----BEGIN PUBLIC KEY-----` |
| **通知地址** | 仅查看，需在支付宝开放平台配置 |

### 3. 保存

点击 **「保存设置」** 完成配置。

---

## 流程说明

```
系统配置
├── recharge_mode = auto
└── payment_driver = alipay
    ├── alipay_app_id = "2021..."
    ├── alipay_private_key = "-----BEGIN RSA PRIVATE KEY-----\n..."
    └── alipay_public_key = "-----BEGIN PUBLIC KEY-----\n..."

用户操作                  系统                      支付宝
─────                    ────                      ────
输入金额 → 点击去支付
                         POST /payment/create/
                         调用支付宝预下单接口 ──────→
                         ←── 返回 qr_code ─────────
显示付款二维码
用户打开支付宝扫码 ←──────
                         用户确认支付 ─────────────→
                         ←── 异步通知 ─────────────
                         POST /payment/notify/
                         验签 → 修改订单状态
                         创建充值记录 → 增加余额

用户看到 "充值成功"
```

---

## 常见问题

### Q: 测试环境如何调试？

开发测试时保持 **支付驱动 = 模拟驱动**，所有操作在系统内完成，无需真实支付宝。

### Q: RSA2 密钥如何生成？

使用支付宝官方提供的 **RSA 密钥生成工具**（[下载](https://opendocs.alipay.com/common/02kipl)）生成：

```bash
# 或使用 OpenSSL 命令行生成
openssl genrsa -out app_private_key.pem 2048
openssl rsa -in app_private_key.pem -pubout -out app_public_key.pem
```

- `app_private_key.pem` → 填入 **应用私钥**
- `app_public_key.pem` → 上传到支付宝开放平台后获取 **支付宝公钥**

### Q: 回调收不到怎么办？

1. 确保服务器公网可达
2. 确认支付宝开放平台配置的 `notify_url` 与实际一致
3. 检查服务器日志：`docker compose logs -f web`
4. 支付宝开放平台支持手动触发回调测试（沙箱环境）

### Q: 需要 HTTPS 吗？

支付宝异步通知要求生产环境使用 HTTPS。Nginx 配置 SSL 证书即可：

```bash
# 使用 certbot 获取免费证书
apt install certbot python3-certbot-nginx
certbot --nginx -d your-domain.com
```

### Q: 支付宝沙箱环境怎么用？

1. 在支付宝开放平台开通 [沙箱应用](https://open.alipay.com/platform/developerIndex.htm)
2. 获取沙箱的 APPID、密钥、支付宝公钥
3. 下载支付宝沙箱版客户端进行扫码测试
4. 在管理后台填写沙箱配置（`debug` 模式下自动使用沙箱环境）

---

## 配置参考

完整的 SystemSetting 配置键：

| 键 | 示例值 | 说明 |
|----|--------|------|
| `recharge_mode` | `auto` | 充值模式：manual / auto |
| `payment_driver` | `alipay` | 支付驱动：simulate / alipay |
| `alipay_app_id` | `2021003126698765` | 支付宝 APPID |
| `alipay_private_key` | `-----BEGIN RSA PRIVATE KEY-----\n...` | 应用私钥 |
| `alipay_public_key` | `-----BEGIN PUBLIC KEY-----\n...` | 支付宝公钥 |

---

## 扩展开发

如需对接其他支付渠道（微信支付、PayPal 等），在 `app/payment/drivers.py` 中新增驱动类：

```python
class WechatPayDriver(PaymentDriver):
    def create_order(self, request, user, amount, out_trade_no):
        # 调微信支付统一下单 API
        pass

    def verify_notification(self, request):
        # 验证微信支付回调签名
        pass
```

然后在管理后台新增 `payment_driver` 选项即可。
