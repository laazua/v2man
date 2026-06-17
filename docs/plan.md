# v2man 生产化实施计划

> **For agentic workers:** 使用 subagent-driven-development 或 executing-plans 逐个任务执行。

**目标：** 将 v2man 从项目骨架完善为可投入生产使用的系统

**架构：** Django + DRF 后端，Vue 3 + Vite 前端，SQLite（开发）/ PostgreSQL（生产），JWT 认证，支付宝个人码充值

**技术栈：** Python 3.13+, Django 6.0, DRF 3.17, Vue 3.5+, Vite 8

---

### Task 1: 生产环境配置

**涉及文件：**
- 修改: `app/config/settings.py`
- 创建: `app/config/settings_prod.py`
- 创建: `app/.env.example`
- 修改: `app/pyproject.toml`

**接口：**
- 输入: 环境变量 `SECRET_KEY`, `DEBUG`, `DATABASE_URL`, `ALLOWED_HOSTS`
- 输出: 可切换开发/生产的 settings 配置

- [ ] **Step 1: 创建 app/.env.example**

```
SECRET_KEY=django-insecure-change-me-in-production
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
# DATABASE_URL=postgres://user:pass@localhost:5432/v2man
ALLOWED_HOSTS=*
CORS_ALLOWED_ORIGINS=http://localhost:5173
STATIC_ROOT=/app/static
```

- [ ] **Step 2: 重写 settings.py 支持环境变量**

```python
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-dev-only-key')
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'users',
    'nodes',
    'plans',
    'traffic',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
import re
_db_url = os.getenv('DATABASE_URL', 'sqlite:///db.sqlite3')
if _db_url.startswith('postgres'):
    import dj_database_url
    DATABASES = {'default': dj_database_url.config(default=_db_url)}
elif _db_url.startswith('sqlite'):
    _match = re.match(r'sqlite:///(.+)', _db_url)
    _path = _match.group(1) if _match else 'db.sqlite3'
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / _path,
        }
    }

AUTH_USER_MODEL = 'users.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = os.getenv('STATIC_ROOT', BASE_DIR / 'staticfiles')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',') if not DEBUG else []

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

- [ ] **Step 3: 安装 dj-database-url**

```bash
cd app && uv add dj-database-url
```

- [ ] **Step 4: 验证 Django 能启动**

```bash
cd app && uv run manage.py check
```


### Task 2: 钱包 + 充值模型

**涉及文件：**
- 创建: `app/users/wallet.py` — Wallet 和 Recharge 模型
- 修改: `app/users/admin.py` — 注册 WalletAdmin, RechargeAdmin
- 修改: `app/users/__init__.py` — 导出
- 执行: makemigrations + migrate

**接口：**
- Wallet: user(O2O), balance(int, 单位分)
- Recharge: user(FK), amount(int, 单位分), status(str: pending/completed), admin_remark(text), created_at, confirmed_at

- [ ] **Step 1: 创建 app/users/wallet.py**

```python
from django.db import models
from django.conf import settings


class Wallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet'
    )
    balance = models.BigIntegerField(default=0, verbose_name='余额(分)')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wallets'
        verbose_name = '钱包'

    def __str__(self) -> str:
        return f'{self.user} ¥{self.balance / 100:.2f}'


class Recharge(models.Model):
    STATUS_CHOICES = [
        ('pending', '待确认'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recharges'
    )
    amount = models.BigIntegerField(verbose_name='金额(分)')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    admin_remark = models.TextField(blank=True, verbose_name='管理员备注')
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name='确认时间')

    class Meta:
        db_table = 'recharges'
        verbose_name = '充值记录'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.user} ¥{self.amount / 100:.2f} ({self.status})'
```

- [ ] **Step 2: 更新 users/admin.py**

```python
from django.contrib import admin
from django.utils import timezone
from .models import User
from .wallet import Wallet, Recharge


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'plan', 'traffic_used', 'traffic_total', 'expire_date', 'is_active']
    list_filter = ['plan', 'is_active']
    search_fields = ['username', 'email']


class RechargeAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount_display', 'status', 'created_at', 'confirmed_at']
    list_filter = ['status']
    actions = ['confirm_recharge']

    @admin.display(description='金额')
    def amount_display(self, obj):
        return f'¥{obj.amount / 100:.2f}'

    def confirm_recharge(self, request, queryset):
        for r in queryset.filter(status='pending'):
            r.status = 'completed'
            r.confirmed_at = timezone.now()
            r.save()
            wallet, _ = Wallet.objects.get_or_create(user=r.user)
            wallet.balance += r.amount
            wallet.save()
        self.message_user(request, f'已确认 {queryset.filter(status="pending").count()} 笔充值')
    confirm_recharge.short_description = '确认选中的充值'

    actions = ['confirm_recharge']


admin.site.register(Wallet)
admin.site.register(Recharge, RechargeAdmin)
```

- [ ] **Step 3: 在 User post_save 中自动创建钱包**

在 users/apps.py 中添加信号，或在 users/__init__.py 中导入。

```python
# users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .wallet import Wallet


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)
```

```python
# users/apps.py
from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        import users.signals
```

- [ ] **Step 4: 迁移**

```bash
cd app && uv run manage.py makemigrations users && uv run manage.py migrate users
```


### Task 3: 套餐 API + 自助购买

**涉及文件：**
- 修改: `app/plans/views.py` — PlanListView, PurchaseView
- 创建: `app/plans/serializers.py` — PlanSerializer, PurchaseSerializer
- 修改: `app/plans/urls.py` — 注册路由
- 修改: `app/config/urls.py` — 引入 plans urls

**接口：**
- GET /api/plans/ → PlanSerializer[] (is_active=True)
- POST /api/plans/purchase/<id>/ → {success, message, balance_remaining}

- [ ] **Step 1: 创建 app/plans/serializers.py**

```python
from rest_framework import serializers
from .models import Plan


class PlanSerializer(serializers.ModelSerializer):
    price_display = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = ['id', 'name', 'price', 'price_display', 'traffic_limit', 'duration_days']

    def get_price_display(self, obj):
        return f'¥{obj.price}'
```

- [ ] **Step 2: 修改 app/plans/views.py**

```python
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from .models import Plan
from .serializers import PlanSerializer
from nodes.subscription import Subscription


class PlanListView(generics.ListAPIView):
    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]


class PurchaseView(APIView):
    def post(self, request, plan_id):
        try:
            plan = Plan.objects.get(id=plan_id, is_active=True)
        except Plan.DoesNotExist:
            return Response({'error': '套餐不存在'}, status=status.HTTP_404_NOT_FOUND)

        wallet = request.user.wallet
        price_cents = int(plan.price * 100)

        if wallet.balance < price_cents:
            return Response({
                'error': '余额不足',
                'balance': wallet.balance,
                'need': price_cents,
            }, status=status.HTTP_400_BAD_REQUEST)

        wallet.balance -= price_cents
        wallet.save()

        user = request.user
        user.plan = plan
        user.traffic_total = user.traffic_total + plan.traffic_limit if plan.traffic_limit > 0 else 0
        user.expire_date = timezone.now() + timezone.timedelta(days=plan.duration_days)
        user.save()

        Subscription.objects.get_or_create(user=user)

        return Response({
            'success': True,
            'message': f'已购买 {plan.name}',
            'balance_remaining': wallet.balance,
        })
```

- [ ] **Step 3: 修改 app/plans/urls.py**

```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.PlanListView.as_view(), name='plan-list'),
    path('purchase/<int:plan_id>/', views.PurchaseView.as_view(), name='plan-purchase'),
]
```

- [ ] **Step 4: 修改 app/config/urls.py**

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/nodes/', include('nodes.urls')),
    path('api/subscription/', include('nodes.urls_sub')),
    path('api/plans/', include('plans.urls')),
    path('api/traffic/', include('traffic.urls')),
]
```

- [ ] **Step 5: 迁移 + 验证**

```bash
cd app && uv run manage.py check
```


### Task 4: 流量 API

**涉及文件：**
- 创建: `app/traffic/serializers.py`
- 修改: `app/traffic/views.py`
- 创建: `app/traffic/urls.py`
- 修改: `app/config/urls.py`（Task 3 已包含）

**接口：**
- POST /api/traffic/record/ → 管理员录入流量 {user_id, upload_bytes, download_bytes, node_name}
- GET /api/traffic/stats/ → 用户查自己流量明细（按日汇总）

- [ ] **Step 1: 创建 app/traffic/serializers.py**

```python
from rest_framework import serializers
from .models import TrafficLog


class TrafficRecordSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    upload_bytes = serializers.IntegerField(min_value=0)
    download_bytes = serializers.IntegerField(min_value=0)
    node_name = serializers.CharField(required=False, allow_blank=True, default='')


class TrafficLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficLog
        fields = ['upload_bytes', 'download_bytes', 'recorded_at', 'node_name']
```

- [ ] **Step 2: 修改 app/traffic/views.py**

```python
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum
from django.db.models.functions import TruncDate
from .models import TrafficLog
from users.models import User
from .serializers import TrafficRecordSerializer, TrafficLogSerializer


class TrafficRecordView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        serializer = TrafficRecordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.get(id=serializer.validated_data['user_id'])
        except User.DoesNotExist:
            return Response({'error': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

        log = TrafficLog.objects.create(
            user=user,
            upload_bytes=serializer.validated_data['upload_bytes'],
            download_bytes=serializer.validated_data['download_bytes'],
            node_name=serializer.validated_data.get('node_name', ''),
        )
        total = serializer.validated_data['upload_bytes'] + serializer.validated_data['download_bytes']
        user.traffic_used = (user.traffic_used or 0) + total // (1024 * 1024)
        user.save(update_fields=['traffic_used'])

        return Response({'success': True, 'id': log.id})


class TrafficStatsView(APIView):
    def get(self, request):
        logs = TrafficLog.objects.filter(user=request.user)
        daily = (
            logs.annotate(date=TruncDate('recorded_at'))
            .values('date')
            .annotate(
                upload=Sum('upload_bytes'),
                download=Sum('download_bytes'),
            )
            .order_by('-date')
        )
        return Response({
            'daily': [
                {
                    'date': str(d['date']),
                    'upload_mb': round(d['upload'] / (1024 * 1024), 2) if d['upload'] else 0,
                    'download_mb': round(d['download'] / (1024 * 1024), 2) if d['download'] else 0,
                }
                for d in daily
            ],
            'total_upload_mb': round(
                logs.aggregate(s=Sum('upload_bytes'))['s'] or 0 / (1024 * 1024), 2
            ),
            'total_download_mb': round(
                logs.aggregate(s=Sum('download_bytes'))['s'] or 0 / (1024 * 1024), 2
            ),
        })
```

- [ ] **Step 3: 创建 app/traffic/urls.py**

```python
from django.urls import path
from . import views

urlpatterns = [
    path('record/', views.TrafficRecordView.as_view(), name='traffic-record'),
    path('stats/', views.TrafficStatsView.as_view(), name='traffic-stats'),
]
```


### Task 5: 订阅信号 + 注册完善

**涉及文件：**
- 修改: `app/users/views.py` — 注册时返回 subscription token
- 修改: `app/users/serializers.py` — Profile 返回订阅链接
- 修改: `app/nodes/subscription.py` — 已有 Subscription 模型

- [ ] **Step 1: 修改 users 注册视图，自动创建 Subscription**

```python
# app/users/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import RegisterSerializer, UserProfileSerializer
from nodes.subscription import Subscription


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        sub, _ = Subscription.objects.get_or_create(user=user)
        return Response({
            'user': UserProfileSerializer(user).data,
            'subscription_token': str(sub.token),
            'message': '注册成功',
        }, status=status.HTTP_201_CREATED)


class ProfileView(APIView):
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        data = serializer.data
        try:
            sub = Subscription.objects.get(user=request.user)
            data['subscription_token'] = str(sub.token)
        except Subscription.DoesNotExist:
            data['subscription_token'] = None
        return Response(data)
```

- [ ] **Step 2: Profile serializers 添加余额**

```python
# app/users/serializers.py
from rest_framework import serializers
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='plan.name', read_only=True, default=None)
    balance = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'uuid', 'plan_name', 'balance',
                  'traffic_used', 'traffic_total', 'expire_date', 'date_joined']

    def get_balance(self, obj):
        wallet = getattr(obj, 'wallet', None)
        return wallet.balance if wallet else 0
```


### Task 6: 前端完善 — 注册页面 + 全局状态

**涉及文件：**
- 创建: `web/src/views/Register.vue`
- 修改: `web/src/router/index.ts` — 添加注册路由
- 修改: `web/src/views/Login.vue` — 添加注册链接
- 修改: `web/src/views/Dashboard.vue` — 显示余额 + 订阅链接复制

- [ ] **Step 1: 创建 Register.vue**

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api, { setTokens } from '../api'

const router = useRouter()
const username = ref('')
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function register() {
  loading.value = true
  error.value = ''
  try {
    await api.post('/auth/register/', {
      username: username.value,
      email: email.value,
      password: password.value,
    })
    // Auto-login after register
    const { data } = await api.post('/auth/login/', {
      username: username.value,
      password: password.value,
    })
    setTokens(data.access, data.refresh)
    router.push('/')
  } catch (e: any) {
    error.value = e.response?.data?.message || '注册失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="register-page">
    <div class="card">
      <h1>注册</h1>
      <form @submit.prevent="register">
        <input v-model="username" placeholder="用户名" required />
        <input v-model="email" type="email" placeholder="邮箱" required />
        <input v-model="password" type="password" placeholder="密码" required minlength="6" />
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" :disabled="loading">{{ loading ? '注册中...' : '注册' }}</button>
      </form>
      <p class="link">已有账号？<router-link to="/login">去登录</router-link></p>
    </div>
  </div>
</template>

<style scoped>
.register-page { display: flex; align-items: center; justify-content: center; height: 100vh; background: #0f172a; }
.card { background: #1e293b; padding: 2rem; border-radius: 8px; width: 320px; }
h1 { color: #e2e8f0; text-align: center; margin-bottom: 1.5rem; }
input { width: 100%; padding: 0.75rem; margin-bottom: 0.75rem; border: 1px solid #334155; border-radius: 4px; background: #0f172a; color: #e2e8f0; }
button { width: 100%; padding: 0.75rem; background: #3b82f6; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
button:disabled { opacity: 0.6; }
.error { color: #ef4444; font-size: 0.875rem; }
.link { text-align: center; margin-top: 1rem; color: #94a3b8; }
.link a { color: #3b82f6; text-decoration: none; }
</style>
```

- [ ] **Step 2: Login 添加注册链接**

在 Login.vue 模板末尾添加：
```html
<p class="link">没有账号？<router-link to="/register">去注册</router-link></p>
```

- [ ] **Step 3: Router 添加注册路由**

```typescript
{ path: '/register', name: 'Register', component: () => import('../views/Register.vue') },
```


### Task 7: 前端充值页

**涉及文件：**
- 创建: `web/src/views/Recharge.vue`
- 修改: `web/src/router/index.ts` — 添加充值路由

- [ ] **Step 1: 创建 Recharge.vue**

```vue
<script setup lang="ts">
import { ref } from 'vue'
import api from '../api'

const amount = ref(0)
const loading = ref(false)
const message = ref('')

async function submitRecharge() {
  if (amount.value < 1) return
  loading.value = true
  message.value = ''
  try {
    await api.post('/auth/recharge/', { amount: amount.value * 100 })
    message.value = `充值 ¥${amount.value} 已提交，等待管理员确认`
    amount.value = 0
  } catch {
    message.value = '提交失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="recharge-page">
    <header>
      <router-link to="/">← 返回</router-link>
      <h2>充值</h2>
    </header>
    <div class="content">
      <div class="qr-section">
        <h3>请使用支付宝扫码付款</h3>
        <div class="qr-placeholder">
          <p>请将支付宝收款码图片放置于此</p>
          <p class="hint">（替换为实际收款码图片）</p>
        </div>
      </div>
      <div class="form-section">
        <h3>或输入充值金额</h3>
        <div class="amount-input">
          <span class="prefix">¥</span>
          <input v-model.number="amount" type="number" min="1" placeholder="输入金额" />
        </div>
        <button @click="submitRecharge" :disabled="loading || amount < 1">
          {{ loading ? '提交中...' : '提交充值' }}
        </button>
        <p v-if="message" class="message">{{ message }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.recharge-page { max-width: 600px; margin: 0 auto; padding: 2rem; color: #e2e8f0; }
header { display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem; }
header a { color: #3b82f6; text-decoration: none; }
.content { display: flex; flex-direction: column; gap: 1.5rem; }
.qr-section, .form-section { background: #1e293b; padding: 1.5rem; border-radius: 8px; }
.qr-placeholder { width: 200px; height: 200px; margin: 1rem auto; background: #334155; display: flex; flex-direction: column; align-items: center; justify-content: center; border-radius: 8px; text-align: center; color: #64748b; font-size: 0.875rem; }
.hint { font-size: 0.75rem; margin-top: 0.5rem; color: #475569; }
.amount-input { display: flex; align-items: center; margin: 1rem 0; }
.prefix { font-size: 1.5rem; margin-right: 0.5rem; color: #94a3b8; }
.amount-input input { flex: 1; padding: 0.75rem; font-size: 1.25rem; border: 1px solid #334155; border-radius: 4px; background: #0f172a; color: #e2e8f0; }
button { width: 100%; padding: 0.75rem; background: #3b82f6; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
button:disabled { opacity: 0.6; }
.message { margin-top: 0.75rem; color: #22c55e; text-align: center; }
</style>
```

- [ ] **Step 2: 后端充值 API**

```python
# app/users/views.py 新增
class RechargeView(APIView):
    def post(self, request):
        amount = request.data.get('amount', 0)
        try:
            amount = int(amount)
        except (ValueError, TypeError):
            return Response({'error': '无效金额'}, status=status.HTTP_400_BAD_REQUEST)
        if amount < 1:
            return Response({'error': '金额必须大于0'}, status=status.HTTP_400_BAD_REQUEST)
        from .wallet import Recharge
        Recharge.objects.create(user=request.user, amount=amount)
        return Response({'success': True, 'message': '充值已提交'})
```

```python
# app/users/urls.py 添加
path('recharge/', views.RechargeView.as_view(), name='recharge'),
```

- [ ] **Step 3: Router 添加充值路由**

```typescript
{ path: '/recharge', name: 'Recharge', component: () => import('../views/Recharge.vue'), meta: { requiresAuth: true } },
```


### Task 8: 前端套餐选购页

**涉及文件：**
- 创建: `web/src/views/Plans.vue`
- 修改: `web/src/router/index.ts`
- 修改: `web/src/views/Dashboard.vue` — 添加套餐链接

- [ ] **Step 1: 创建 Plans.vue**

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'

interface Plan {
  id: number
  name: string
  price_display: string
  traffic_limit: number
  duration_days: number
}

const plans = ref<Plan[]>([])
const balance = ref(0)
const error = ref('')
const success = ref('')
const buying = ref<number | null>(null)

onMounted(async () => {
  const [planRes, profileRes] = await Promise.all([
    api.get('/plans/'),
    api.get('/auth/profile/'),
  ])
  plans.value = planRes.data
  balance.value = profileRes.data.balance
})

function formatTraffic(mb: number): string {
  if (mb === 0) return '无限'
  if (mb >= 1024) return `${(mb / 1024).toFixed(0)} GB`
  return `${mb} MB`
}

async function buy(plan: Plan) {
  buying.value = plan.id
  error.value = ''
  success.value = ''
  try {
    const { data } = await api.post(`/plans/purchase/${plan.id}/`)
    success.value = data.message
    balance.value = data.balance_remaining
  } catch (e: any) {
    error.value = e.response?.data?.error || '购买失败'
  } finally {
    buying.value = null
  }
}
</script>

<template>
  <div class="plans-page">
    <header>
      <router-link to="/">← 返回</router-link>
      <h2>选择套餐</h2>
      <span class="balance">余额: ¥{{ (balance / 100).toFixed(2) }}</span>
    </header>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="success" class="success">{{ success }}</p>
    <div class="plan-list">
      <div v-for="plan in plans" :key="plan.id" class="plan-card">
        <h3>{{ plan.name }}</h3>
        <p class="price">{{ plan.price_display }}</p>
        <p class="detail">{{ formatTraffic(plan.traffic_limit) }} / {{ plan.duration_days }} 天</p>
        <button @click="buy(plan)" :disabled="buying === plan.id">
          {{ buying === plan.id ? '购买中...' : '购买' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.plans-page { max-width: 800px; margin: 0 auto; padding: 2rem; color: #e2e8f0; }
header { display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem; }
header a { color: #3b82f6; text-decoration: none; }
.balance { margin-left: auto; color: #22c55e; }
.plan-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 1rem; }
.plan-card { background: #1e293b; padding: 1.5rem; border-radius: 8px; text-align: center; }
.plan-card h3 { margin: 0 0 0.5rem; }
.price { font-size: 1.5rem; color: #f59e0b; margin: 0.5rem 0; }
.detail { color: #64748b; font-size: 0.875rem; margin-bottom: 1rem; }
button { width: 100%; padding: 0.75rem; background: #3b82f6; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
button:disabled { opacity: 0.6; }
.error { color: #ef4444; }
.success { color: #22c55e; }
</style>
```

- [ ] **Step 2: Router 添加套餐路由**

```typescript
{ path: '/plans', name: 'Plans', component: () => import('../views/Plans.vue'), meta: { requiresAuth: true } },
```


### Task 9: 仪表盘升级 + 节点页升级

**涉及文件：**
- 修改: `web/src/views/Dashboard.vue`
- 修改: `web/src/views/Nodes.vue`

- [ ] **Step 1: 升级 Dashboard.vue**

添加余额显示、订阅链接（三种格式）复制、流量进度条、到套餐选购和充值的链接。

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'
import type { User } from '../types'

const origin = window.location.origin
const user = ref<(User & { subscription_token?: string; balance?: number }) | null>(null)

onMounted(async () => {
  const { data } = await api.get('/auth/profile/')
  user.value = data
})

function formatMB(mb: number): string {
  if (mb >= 1024) return `${(mb / 1024).toFixed(1)} GB`
  return `${mb} MB`
}

function formatBalance(cents: number): string {
  return `¥${(cents / 100).toFixed(2)}`
}

function trafficPercent(): number {
  if (!user.value || !user.value.traffic_total) return 0
  return Math.min(100, Math.round((user.value.traffic_used / user.value.traffic_total) * 100))
}

function copy(text: string) {
  navigator.clipboard.writeText(text)
}

function logout() {
  localStorage.clear()
  window.location.href = '/login'
}
</script>

<template>
  <div class="dashboard">
    <header>
      <h2>v2man</h2>
      <div class="header-right">
        <span class="balance" v-if="user">余额: {{ formatBalance(user.balance || 0) }}</span>
        <button @click="logout">退出</button>
      </div>
    </header>

    <div v-if="user" class="grid">
      <div class="card">
        <h3>当前套餐</h3>
        <p>{{ user.plan_name || '无套餐' }}</p>
        <router-link to="/plans">购买套餐 →</router-link>
      </div>

      <div class="card">
        <h3>使用量</h3>
        <p>{{ formatMB(user.traffic_used) }} / {{ formatMB(user.traffic_total) }}</p>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: trafficPercent() + '%' }"></div>
        </div>
      </div>

      <div class="card">
        <h3>到期时间</h3>
        <p>{{ user.expire_date ? new Date(user.expire_date).toLocaleDateString('zh-CN') : '无' }}</p>
      </div>

      <div class="card">
        <h3>充值</h3>
        <router-link to="/recharge">去充值 →</router-link>
      </div>
    </div>

    <div v-if="user?.subscription_token" class="subscribe-section">
      <h3>订阅链接</h3>
      <div class="sub-links">
        <div class="sub-item">
          <label>V2Ray (Base64)</label>
          <code>{{ origin }}/api/subscription/{{ user.subscription_token }}/</code>
          <button @click="copy(`${origin}/api/subscription/${user.subscription_token}/`)">复制</button>
        </div>
        <div class="sub-item">
          <label>Clash</label>
          <code>{{ origin }}/api/subscription/{{ user.subscription_token }}/?format=clash</code>
          <button @click="copy(`${origin}/api/subscription/${user.subscription_token}/?format=clash`)">复制</button>
        </div>
        <div class="sub-item">
          <label>Sing-box</label>
          <code>{{ origin }}/api/subscription/{{ user.subscription_token }}/?format=singbox</code>
          <button @click="copy(`${origin}/api/subscription/${user.subscription_token}/?format=singbox`)">复制</button>
        </div>
      </div>
    </div>

    <div class="nav-links">
      <router-link to="/nodes">节点列表 →</router-link>
    </div>
  </div>
</template>

<style scoped>
.dashboard { max-width: 800px; margin: 0 auto; padding: 2rem; color: #e2e8f0; }
header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
.header-right { display: flex; align-items: center; gap: 1rem; }
.balance { color: #22c55e; }
.grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
.card { background: #1e293b; padding: 1.25rem; border-radius: 8px; }
.card h3 { margin: 0 0 0.5rem; font-size: 0.875rem; color: #94a3b8; }
.card p { margin: 0 0 0.75rem; font-size: 1.125rem; }
.card a { color: #3b82f6; text-decoration: none; font-size: 0.875rem; }
.progress-bar { height: 6px; background: #334155; border-radius: 3px; overflow: hidden; }
.progress-fill { height: 100%; background: #3b82f6; border-radius: 3px; transition: width 0.3s; }
.subscribe-section { background: #1e293b; padding: 1.25rem; border-radius: 8px; margin-bottom: 1.5rem; }
.sub-item { display: flex; align-items: center; gap: 0.5rem; margin-top: 0.75rem; flex-wrap: wrap; }
.sub-item label { font-size: 0.8rem; color: #94a3b8; min-width: 100px; }
.sub-item code { flex: 1; font-size: 0.75rem; word-break: break-all; color: #e2e8f0; background: #0f172a; padding: 0.25rem 0.5rem; border-radius: 4px; }
.sub-item button { background: #3b82f6; color: #fff; border: none; padding: 0.25rem 0.5rem; border-radius: 4px; cursor: pointer; font-size: 0.75rem; }
.nav-links { margin-top: 1rem; }
.nav-links a { color: #3b82f6; text-decoration: none; }
button { background: #ef4444; color: #fff; border: none; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer; }
</style>
```

- [ ] **Step 2: 升级 Nodes.vue**

从 profile API 获取真实 subscription_token，展示三种格式链接。

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'
import type { Node } from '../types'

const origin = window.location.origin
const nodes = ref<Node[]>([])
const subToken = ref('')

onMounted(async () => {
  const [nodeRes, profileRes] = await Promise.all([
    api.get('/nodes/'),
    api.get('/auth/profile/'),
  ])
  nodes.value = nodeRes.data
  subToken.value = profileRes.data.subscription_token || ''
})

function copy(text: string) {
  navigator.clipboard.writeText(text)
}
</script>

<template>
  <div class="nodes-page">
    <header>
      <router-link to="/">← 返回</router-link>
      <h2>节点列表</h2>
    </header>

    <div v-if="subToken" class="subscribe-box">
      <h3>订阅链接</h3>
      <div class="sub-item">
        <label>V2Ray</label>
        <code>{{ origin }}/api/subscription/{{ subToken }}/</code>
        <button @click="copy(`${origin}/api/subscription/${subToken}/`)">复制</button>
      </div>
      <div class="sub-item">
        <label>Clash</label>
        <code>{{ origin }}/api/subscription/{{ subToken }}/?format=clash</code>
        <button @click="copy(`${origin}/api/subscription/${subToken}/?format=clash`)">复制</button>
      </div>
      <div class="sub-item">
        <label>Sing-box</label>
        <code>{{ origin }}/api/subscription/{{ subToken }}/?format=singbox</code>
        <button @click="copy(`${origin}/api/subscription/${subToken}/?format=singbox`)">复制</button>
      </div>
    </div>

    <div class="node-list">
      <div v-for="node in nodes" :key="node.id" class="node-card">
        <div class="node-header">
          <span class="protocol">{{ node.protocol }}</span>
          <strong>{{ node.name }}</strong>
        </div>
        <div class="node-info">{{ node.address }}:{{ node.port }}</div>
      </div>
      <p v-if="!nodes.length" class="empty">暂无可用节点</p>
    </div>
  </div>
</template>

<style scoped>
.nodes-page { max-width: 800px; margin: 0 auto; padding: 2rem; color: #e2e8f0; }
header { display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem; }
header a { color: #3b82f6; text-decoration: none; }
.subscribe-box { background: #1e293b; padding: 1.25rem; border-radius: 8px; margin-bottom: 1.5rem; }
.sub-item { display: flex; align-items: center; gap: 0.5rem; margin-top: 0.75rem; flex-wrap: wrap; }
.sub-item label { font-size: 0.8rem; color: #94a3b8; min-width: 60px; }
.sub-item code { flex: 1; font-size: 0.75rem; word-break: break-all; color: #e2e8f0; background: #0f172a; padding: 0.25rem 0.5rem; border-radius: 4px; }
.sub-item button { background: #3b82f6; color: #fff; border: none; padding: 0.25rem 0.5rem; border-radius: 4px; cursor: pointer; font-size: 0.75rem; }
.node-list { display: grid; gap: 0.75rem; }
.node-card { background: #1e293b; padding: 1rem; border-radius: 8px; }
.node-header { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem; }
.protocol { background: #334155; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; color: #94a3b8; }
.node-info { color: #64748b; font-size: 0.875rem; }
.empty { text-align: center; color: #64748b; padding: 2rem; }
</style>
```


### Task 10: 管理命令 + 部署配置

**涉及文件：**
- 创建: `app/users/management/commands/check_expired.py`
- 创建: `app/users/management/commands/reset_traffic.py`
- 创建: `Dockerfile`
- 创建: `docker-compose.yml`
- 创建: `nginx.conf`
- 修改: `app/pyproject.toml`

- [ ] **Step 1: 创建管理命令目录**

```bash
mkdir -p app/users/management/commands && touch app/users/management/__init__.py app/users/management/commands/__init__.py
```

- [ ] **Step 2: check_expired.py**

```python
from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import User


class Command(BaseCommand):
    help = '检查到期用户并自动停用'

    def handle(self, *args, **options):
        now = timezone.now()
        expired = User.objects.filter(
            is_active=True, expire_date__isnull=False, expire_date__lte=now
        )
        count = expired.count()
        expired.update(is_active=False)
        self.stdout.write(self.style.SUCCESS(f'已停用 {count} 个到期用户'))
```

- [ ] **Step 3: 修改 pyproject.toml 添加 gunicorn**

```bash
cd app && uv add gunicorn
```

- [ ] **Step 4: 创建 Dockerfile**

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY app/ .
RUN pip install uv && uv sync --frozen
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uv", "run", "gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

- [ ] **Step 5: 创建 docker-compose.yml**

```yaml
services:
  web:
    build: .
    ports:
      - "8000:8000"
    env_file: app/.env
    depends_on:
      - db
    volumes:
      - static:/app/staticfiles
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: v2man
      POSTGRES_USER: v2man
      POSTGRES_PASSWORD: v2man
    volumes:
      - pgdata:/var/lib/postgresql/data
volumes:
  pgdata:
  static:
```

- [ ] **Step 6: 创建 nginx.conf**

```nginx
server {
    listen 80;
    server_name _;
    location /api/ { proxy_pass http://web:8000; }
    location /admin/ { proxy_pass http://web:8000; }
    location /static/ { alias /app/staticfiles/; }
    location / { root /app/web/dist; try_files $uri $uri/ /index.html; }
}
```


### Task 11: 修复 Vite 代理 + 清理脚手架文件

**涉及文件：**
- 修改: `web/vite.config.ts` — 修复代理端口
- 删除: `web/src/components/HelloWorld.vue`
- 删除: `web/src/assets/hero.png`
- 删除: `web/src/assets/vue.svg`
- 删除: `web/src/assets/vite.svg`

- [ ] **Step 1: 修复 vite.config.ts**

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
```

- [ ] **Step 2: 清理脚手架残留**

```bash
rm -f web/src/components/HelloWorld.vue web/src/assets/hero.png web/src/assets/vue.svg web/src/assets/vite.svg
```


### Task 12: 最终验证

**涉及文件：**
- 无需修改，运行验证

- [ ] **Step 1: 运行后端检查**

```bash
cd app && uv run manage.py check
```

- [ ] **Step 2: 前端构建检查**

```bash
cd web && npm run build
```
