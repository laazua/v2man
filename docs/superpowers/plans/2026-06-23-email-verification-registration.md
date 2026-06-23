# 邮箱验证码注册 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将注册改为"先注册再激活"流程，解决注册 429 限流问题

**Architecture:** 注册时创建 `is_active=False` 用户，发送 6 位验证码到邮箱；验证码存缓存（5 分钟有效）；提交验证码激活账号；移除注册限流，新增验证码发送限流 `1/minute`

**Tech Stack:** Django 5, DRF, SimpleJWT, Vue 3, TypeScript

## Global Constraints

- `is_active=False` 的用户不可登录（SimpleJWT 默认行为）
- 验证码存储于 `LocMemCache`，key 格式 `verify_code_{email}`
- 验证码为 6 位随机数字（`secrets.randbelow(10**6)` 补零）
- 前端注册成功后跳转到验证页（无需自动登录）

---

### Task 1: 后端 - 修改 throttles.py

**Files:**
- Modify: `app/users/throttles.py`（整文件）

- [ ] **Step 1: 移除 RegisterThrottle，添加 VerificationCodeThrottle**

```python
"""Custom throttle classes for rate-limiting API endpoints."""

from rest_framework.throttling import SimpleRateThrottle


class LoginThrottle(SimpleRateThrottle):
    """Rate-limit login attempts for unauthenticated users."""

    scope = 'login'

    def get_cache_key(self, request, view):
        """Generate cache key using client IP for anonymous users only."""
        if request.user.is_authenticated:
            return None
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request),
        }


class PasswordResetThrottle(SimpleRateThrottle):
    """Rate-limit password reset requests."""

    scope = 'password_reset'

    def get_cache_key(self, request, view):
        """Generate cache key using client IP."""
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request),
        }


class VerificationCodeThrottle(SimpleRateThrottle):
    """Rate-limit verification code sending requests."""

    scope = 'verification_code'

    def get_cache_key(self, request, view):
        email = request.data.get('email', '')
        return self.cache_format % {
            'scope': self.scope,
            'ident': email or self.get_ident(request),
        }
```

- [ ] **Step 2: Commit**

```bash
git add app/users/throttles.py
git commit -m "refactor: 移除注册限流，新增验证码发送限流"
```

---

### Task 2: 后端 - 修改 settings.py

**Files:**
- Modify: `app/config/settings.py`

- [ ] **Step 1: 更新 throttle rates**

在 `settings.py:211-217`，替换为：

```python
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/hour',
        'user': '1000/hour',
        'login': '10/minute',
        'password_reset': '5/hour',
        'verification_code': '1/minute',
    },
```

- [ ] **Step 2: 提交**

```bash
git add app/config/settings.py
git commit -m "feat: 更新限流配置，移除注册限流，新增验证码限流"
```

---

### Task 3: 后端 - 修改 serializers.py

**Files:**
- Modify: `app/users/serializers.py`

- [ ] **Step 1: 新增 ActivateSerializer**

在文件末尾添加：

```python
class ActivateSerializer(serializers.Serializer):
    """Serializer for email verification code activation."""

    email = serializers.EmailField()
    code = serializers.CharField(min_length=6, max_length=6)
```

- [ ] **Step 2: 提交**

```bash
git add app/users/serializers.py
git commit -m "feat: 新增 ActivateSerializer"
```

---

### Task 4: 后端 - 修改 views.py

**Files:**
- Modify: `app/users/views.py`

- [ ] **Step 1: 在 RegisterView.create() 中发送验证码**

修改 `RegisterView`，在创建用户后发送验证码：

```python
import random

class RegisterView(generics.CreateAPIView):
    """Handle user registration with email verification."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user.is_active = False
        user.save()

        code_str = serializer.validated_data.get('invite_code', '')
        if code_str:
            try:
                code = InviteCode.objects.get(code=code_str, is_active=True)
                if code.owner != user:
                    Referral.objects.create(
                        inviter=code.owner, invited=user, invite_code=code,
                    )
            except InviteCode.DoesNotExist:
                pass

        # 生成并发送验证码
        email = user.email
        verify_code = f'{random.randrange(0, 10**6):06d}'
        cache.set(f'verify_code_{email}', verify_code, 300)

        try:
            send_mail(
                'v2man 邮箱验证',
                f'您的验证码是：{verify_code}\n\n'
                f'验证码 5 分钟内有效。如果您没有注册 v2man，请忽略此邮件。',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
        except Exception:
            logger.warning('验证码发送失败: email=%s', email)

        logger.info('用户注册: id=%s username=%s email=%s invite_code=%s',
                     user.id, user.username, email, code_str or '无')
        return Response({
            'user': UserProfileSerializer(user).data,
            'message': '注册成功，请查看邮箱输入验证码完成激活',
        }, status=status.HTTP_201_CREATED)
```

- [ ] **Step 2: 新增 ActivateView**

在 `RegisterView` 之后（`ProfileView` 之前）添加：

```python
class ActivateView(APIView):
    """Activate user account with verification code."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ActivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        cached_code = cache.get(f'verify_code_{email}')
        if not cached_code:
            return Response(
                {'error': '验证码已过期，请重新获取'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if cached_code != code:
            return Response(
                {'error': '验证码错误'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email, is_active=False)
        except User.DoesNotExist:
            return Response(
                {'error': '该邮箱未注册或已激活'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_active = True
        user.save()
        cache.delete(f'verify_code_{email}')

        logger.info('用户激活: id=%s email=%s', user.id, email)
        return Response({
            'message': '邮箱验证成功，请登录',
        })
```

- [ ] **Step 3: 新增 ResendCodeView**

在 `ActivateView` 之后添加：

```python
class ResendCodeView(APIView):
    """Resend verification code to user's email."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '')

        try:
            user = User.objects.get(email=email, is_active=False)
        except User.DoesNotExist:
            return Response(
                {'error': '该邮箱未注册或已激活'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        verify_code = f'{random.randrange(0, 10**6):06d}'
        cache.set(f'verify_code_{email}', verify_code, 300)

        try:
            send_mail(
                'v2man 邮箱验证',
                f'您的验证码是：{verify_code}\n\n'
                f'验证码 5 分钟内有效。如果您没有注册 v2man，请忽略此邮件。',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
        except Exception:
            return Response(
                {'error': '邮件发送失败，请检查邮箱配置'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        logger.info('验证码重新发送: email=%s', email)
        return Response({'message': '验证码已重新发送到您的邮箱'})
```

- [ ] **Step 4: 更新 import**

确保 `views.py` 顶部 imort 包含 `random`、`ActivateSerializer`：

```python
import random

from .serializers import (
    ActivateSerializer,
    PaymentOrderSerializer,
    RegisterSerializer,
    RechargeSerializer,
    UserProfileSerializer,
)
```

- [ ] **Step 5: 提交**

```bash
git add app/users/views.py
git commit -m "feat: 注册发送验证码，新增激活和重发接口"
```

---

### Task 5: 后端 - 修改 urls.py

**Files:**
- Modify: `app/users/urls.py`

- [ ] **Step 1: 更新 import 和路由**

更新 import（移除 `RegisterThrottle`，添加 `VerificationCodeThrottle`）：

```python
from .throttles import (
    LoginThrottle,
    PasswordResetThrottle,
    VerificationCodeThrottle,
)
```

修改注册路由（移除 `RegisterThrottle`），在 `urlpatterns` 末尾添加新路由：

```python
    path('register/', views.RegisterView.as_view(), name='register'),
    path('activate/', views.ActivateView.as_view(), name='activate'),
    path('verification-code/resend/', views.ResendCodeView.as_view(
        throttle_classes=[VerificationCodeThrottle],
    ), name='resend-code'),
```

- [ ] **Step 2: 提交**

```bash
git add app/users/urls.py
git commit -m "feat: 新增激活和重发送验证码路由"
```

---

### Task 6: 后端 - 编写测试

**Files:**
- Create: `app/users/tests/test_verification.py`

- [ ] **Step 1: 编写测试文件**

```python
"""Tests for email verification registration flow."""

import time
from django.core import mail
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from users.models import User


class VerificationRegistrationTest(TestCase):
    """Test email verification during registration."""

    def setUp(self):
        self.client = APIClient()
        self.register_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
        }

    def test_register_creates_inactive_user_and_sends_code(self):
        """注册后用户为未激活状态，且收到验证码邮件"""
        resp = self.client.post('/api/auth/register/', self.register_data)
        self.assertEqual(resp.status_code, 201)
        user = User.objects.get(username='testuser')
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('验证码', mail.outbox[0].subject)

    def test_activate_with_valid_code(self):
        """有效验证码可激活用户"""
        self.client.post('/api/auth/register/', self.register_data)
        user = User.objects.get(username='testuser')
        # 从邮件提取验证码
        body = mail.outbox[0].body
        code = body.split('验证码是：')[1].split('\n')[0].strip()

        resp = self.client.post('/api/auth/activate/', {
            'email': 'test@example.com',
            'code': code,
        })
        self.assertEqual(resp.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_activate_wrong_code(self):
        """错误验证码返回 400"""
        self.client.post('/api/auth/register/', self.register_data)
        resp = self.client.post('/api/auth/activate/', {
            'email': 'test@example.com',
            'code': '000000',
        })
        self.assertEqual(resp.status_code, 400)

    def test_activate_expired_code(self):
        """过期验证码返回 400"""
        self.client.post('/api/auth/register/', self.register_data)
        user = User.objects.get(username='testuser')
        # 模拟过期
        from django.core.cache import cache
        cache.delete(f'verify_code_{user.email}')
        resp = self.client.post('/api/auth/activate/', {
            'email': 'test@example.com',
            'code': '123456',
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn('已过期', resp.json()['error'])

    def test_inactive_user_cannot_login(self):
        """未激活用户无法登录"""
        self.client.post('/api/auth/register/', self.register_data)
        resp = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123',
        })
        self.assertEqual(resp.status_code, 401)

    def test_resend_code(self):
        """重发验证码接口发送新验证码"""
        self.client.post('/api/auth/register/', self.register_data)
        # 清空邮件列表，模拟第一次邮件已发送
        mail.outbox = []
        resp = self.client.post('/api/auth/verification-code/resend/', {
            'email': 'test@example.com',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('验证码', mail.outbox[0].subject)
```

- [ ] **Step 2: 运行测试**

Run: `cd /opt/codes/v2man/app && uv run manage.py test users.tests.test_verification -v 2`
Expected: 6 tests pass

- [ ] **Step 3: 提交**

```bash
git add app/users/tests/test_verification.py
git commit -m "test: 邮箱验证码注册流程测试"
```

---

### Task 7: 前端 - 新增激活页面 VerifyCode.vue

**Files:**
- Create: `web/src/views/VerifyCode.vue`

- [ ] **Step 1: 创建验证码页**

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../api'

const router = useRouter()
const route = useRoute()
const email = ref((route.query.email as string) || '')
const code = ref('')
const error = ref('')
const success = ref('')
const loading = ref(false)
const resendLoading = ref(false)
const cooldown = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  if (!email.value) {
    error.value = '缺少邮箱信息，请重新注册'
  }
})

function startCooldown() {
  cooldown.value = 60
  timer = setInterval(() => {
    cooldown.value--
    if (cooldown.value <= 0) {
      if (timer) clearInterval(timer)
    }
  }, 1000)
}

async function activate() {
  if (!code.value || code.value.length !== 6) return
  loading.value = true
  error.value = ''
  success.value = ''
  try {
    await api.post('/auth/activate/', { email: email.value, code: code.value })
    success.value = '邮箱验证成功！即将跳转登录页...'
    setTimeout(() => router.push('/login'), 2000)
  } catch (e: any) {
    error.value = e.response?.data?.error || '验证失败'
  } finally {
    loading.value = false
  }
}

async function resend() {
  if (cooldown.value > 0) return
  resendLoading.value = true
  error.value = ''
  try {
    await api.post('/auth/verification-code/resend/', { email: email.value })
    startCooldown()
    error.value = ''
  } catch (e: any) {
    error.value = e.response?.data?.error || '发送失败'
  } finally {
    resendLoading.value = false
  }
}
</script>

<template>
  <div class="verify-page">
    <div class="verify-card">
      <div class="icon-area">
        <div class="mail-icon">✉</div>
      </div>
      <h1>验证邮箱</h1>
      <p class="desc">验证码已发送至 <strong>{{ email }}</strong></p>
      <form @submit.prevent="activate">
        <div class="code-inputs">
          <input
            v-model="code"
            type="text"
            maxlength="6"
            placeholder="输入验证码"
            class="code-input"
            autocomplete="one-time-code"
            inputmode="numeric"
            pattern="[0-9]*"
          />
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <p v-if="success" class="success">{{ success }}</p>
        <button type="submit" :disabled="loading || code.length !== 6" class="verify-btn">
          {{ loading ? '验证中...' : '验证' }}
        </button>
      </form>
      <p class="resend">
        <button
          @click="resend"
          :disabled="resendLoading || cooldown > 0"
          class="resend-btn"
        >
          {{ cooldown > 0 ? `重新发送 (${cooldown}s)` : '重新发送验证码' }}
        </button>
      </p>
      <p class="link"><router-link to="/login">去登录</router-link></p>
    </div>
  </div>
</template>

<style scoped>
.verify-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(180deg, #dbeafe 0%, #eff6ff 30%, #f0fdf4 70%, #fefce8 100%);
}
.verify-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  padding: 2.5rem;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  width: 380px;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.06);
  text-align: center;
}
.icon-area { margin-bottom: 1rem; }
.mail-icon {
  width: 60px;
  height: 60px;
  margin: 0 auto;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: #fff;
}
h1 { color: #1e293b; font-size: 1.5rem; font-weight: 700; margin: 0 0 0.5rem; }
.desc { color: #64748b; font-size: 0.9rem; margin: 0 0 1.5rem; }
.desc strong { color: #1e293b; }
.code-inputs { margin-bottom: 1rem; }
.code-input {
  width: 100%;
  padding: 0.8rem 1rem;
  border: 1.5px solid #e2e8f0;
  border-radius: 12px;
  font-size: 1.5rem;
  text-align: center;
  letter-spacing: 0.5em;
  outline: none;
  transition: border-color 0.2s;
}
.code-input:focus { border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.08); }
.error { color: #ef4444; font-size: 0.8rem; margin: 0 0 0.75rem; }
.success { color: #22c55e; font-size: 0.8rem; margin: 0 0 0.75rem; }
.verify-btn {
  width: 100%;
  padding: 0.8rem;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  color: #fff;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 600;
  transition: all 0.25s;
}
.verify-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 8px 24px rgba(59,130,246,0.25); }
.verify-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.resend { margin-top: 1rem; }
.resend-btn {
  background: none;
  border: none;
  color: #3b82f6;
  cursor: pointer;
  font-size: 0.85rem;
  text-decoration: underline;
}
.resend-btn:disabled { color: #94a3b8; cursor: not-allowed; text-decoration: none; }
.link { margin-top: 1rem; }
.link a { color: #3b82f6; text-decoration: none; font-size: 0.85rem; }
</style>
```

- [ ] **Step 2: 提交**

```bash
git add web/src/views/VerifyCode.vue
git commit -m "feat: 新增邮箱验证码页面"
```

---

### Task 8: 前端 - 修改 Register.vue

**Files:**
- Modify: `web/src/views/Register.vue`

- [ ] **Step 1: 注册成功后跳转到验证页**

修改 `<script>` 部分，注册成功后不再自动登录，而是跳转到验证码页：

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../api'
import { useSiteName } from '../api/site'

const router = useRouter()
const route = useRoute()
const siteName = useSiteName()
const username = ref('')
const email = ref('')
const password = ref('')
const showPwd = ref(false)
const error = ref('')
const loading = ref(false)
const inviteCode = ref((route.query.invite as string) || '')

async function register() {
  loading.value = true
  error.value = ''
  try {
    const payload: Record<string, any> = {
      username: username.value,
      email: email.value,
      password: password.value,
    }
    if (inviteCode.value) payload.invite_code = inviteCode.value
    await api.post('/auth/register/', payload)
    router.push(`/verify?email=${encodeURIComponent(email.value)}`)
  } catch (e: any) {
    error.value = e.response?.data?.message || '注册失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>
```

- [ ] **Step 2: 提交**

```bash
git add web/src/views/Register.vue
git commit -m "feat: 注册成功后跳转验证码页"
```

---

### Task 9: 前端 - 修改 router/index.ts

**Files:**
- Modify: `web/src/router/index.ts`

- [ ] **Step 1: 添加验证码路由**

在 `'/register'` 路由后添加：

```typescript
  { path: '/verify', name: 'Verify', component: () => import('../views/VerifyCode.vue') },
```

- [ ] **Step 2: 提交**

```bash
git add web/src/router/index.ts
git commit -m "feat: 新增验证码页面路由"
```

---

### Task 10: 前端 - 修改 Login.vue 处理未激活提示

**Files:**
- Modify: `web/src/views/Login.vue`

- [ ] **Step 1: 登录失败时增加未激活提示**

在 `Login.vue` 的 catch 块中，修改 401 处理：

```typescript
    if (e.response?.status === 401) {
      error.value = '用户名或密码错误'
      // 如果用户未激活，尝试给出更具体的提示（可选）
    }
```

保持现有逻辑不变（401 返回统一错误信息，不暴露账号是否存在）。

- [ ] **Step 2: 提交**

```bash
git add web/src/views/Login.vue
git commit -m "chore: 登录保持原逻辑，未激活用户统一返回错误"
```
