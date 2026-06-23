"""Views for authentication, profile, recharge, and payment handling."""

import hashlib
import logging
import mimetypes
import secrets
import time
from typing import Any

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.cache import cache
from django.core.mail import send_mail
from django.http import FileResponse
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from invite.models import InviteCode, Referral, SystemSetting
from nodes.subscription import Subscription
from payment.drivers import get_payment_driver

from .models import User
from .serializers import (
    PaymentOrderSerializer,
    RegisterSerializer,
    RechargeSerializer,
    UserProfileSerializer,
)
from .wallet import PaymentConfig, PaymentOrder, Recharge, Wallet

logger = logging.getLogger('business')
token_generator = PasswordResetTokenGenerator()


class RegisterView(generics.CreateAPIView):
    """Handle user registration with optional invite code."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(
        self,
        request: Request,
        *args: Any,
        **kwargs: Any,
    ) -> Response:
        """Register a new user and process invite code if provided."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

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

        logger.info(
            '用户注册: id=%s username=%s invite_code=%s',
            user.id, user.username, code_str or '无',
        )
        return Response({
            'user': UserProfileSerializer(user).data,
            'message': '注册成功',
        }, status=status.HTTP_201_CREATED)


class ProfileView(APIView):
    """View and update the current user's profile."""

    def get(self, request: Request) -> Response:
        """Return current user profile with subscription token."""
        serializer = UserProfileSerializer(request.user)
        data = serializer.data
        try:
            sub = Subscription.objects.get(user=request.user)
            data['subscription_token'] = str(sub.token)
        except Subscription.DoesNotExist:
            data['subscription_token'] = None
        return Response(data)

    def patch(self, request: Request) -> Response:
        """Update email and/or password for the current user."""
        user = request.user
        email = request.data.get('email')
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        changed = []
        if email is not None:
            user.email = email
            changed.append('email')
        if new_password:
            if not old_password or not user.check_password(old_password):
                return Response(
                    {'error': '原密码不正确'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.set_password(new_password)
            changed.append('password')
        user.save()
        logger.info('用户资料更新: id=%s changed=%s', user.id, changed)
        return Response(UserProfileSerializer(user).data)


class RechargeView(APIView):
    """View recharge history or submit a new recharge request."""

    def get(self, request: Request) -> Response:
        """Return recharge history ordered by creation time."""
        recharges = Recharge.objects.filter(
            user=request.user,
        ).order_by('-created_at')
        return Response(RechargeSerializer(recharges, many=True).data)

    def post(self, request: Request) -> Response:
        """Submit a new manual recharge request."""
        if Recharge.objects.filter(
            user=request.user, status='pending',
        ).exists():
            return Response(
                {'error': '请扫码付款，如果付款未到账，联系管理员进行处理'},
                status=400,
            )
        amount = request.data.get('amount', 0)
        try:
            amount = int(amount)
        except (ValueError, TypeError):
            return Response(
                {'error': '无效金额'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if amount < 1:
            return Response(
                {'error': '金额必须大于0'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        Recharge.objects.create(user=request.user, amount=amount)
        logger.info(
            '用户提交充值: user_id=%s amount=%s', request.user.id, amount,
        )
        return Response({
            'success': True, 'message': '充值已提交，等待管理员确认',
        })


class PaymentModeView(APIView):
    """Return the current payment mode (manual or auto)."""

    permission_classes = [permissions.AllowAny]

    def get(self, request: Request) -> Response:
        """Return the recharge mode setting."""
        mode = SystemSetting.get('recharge_mode', 'manual')
        return Response({'recharge_mode': mode})


class PaymentCreateView(APIView):
    """Create a payment order in auto-recharge mode."""

    def post(self, request: Request) -> Response:
        """Create payment order and return payment details."""
        mode = SystemSetting.get('recharge_mode', 'manual')
        if mode != 'auto':
            return Response(
                {'error': '当前为手动充值模式'}, status=400,
            )

        amount = request.data.get('amount', 0)
        try:
            amount = int(amount)
        except (ValueError, TypeError):
            return Response({'error': '无效金额'}, status=400)
        if amount < 1:
            return Response({'error': '金额必须大于0'}, status=400)

        out_trade_no = (
            f'PAY{int(time.time())}{secrets.token_hex(4).upper()}'
        )

        driver = get_payment_driver(request)
        try:
            result = driver.create_order(
                request, request.user, amount, out_trade_no,
            )
        except Exception as e:
            return Response({'error': str(e)}, status=400)

        order = PaymentOrder.objects.create(
            user=request.user,
            amount=amount,
            out_trade_no=out_trade_no,
        )

        logger.info(
            '创建支付订单: user_id=%s amount=%s out_trade_no=%s '
            'driver=%s',
            request.user.id, amount, out_trade_no,
            SystemSetting.get('payment_driver', 'simulate'),
        )
        data = PaymentOrderSerializer(order).data
        data.update(result)
        return Response(data, status=201)


class PaymentNotifyView(APIView):
    """Handle payment notifications from the payment driver."""

    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> Response:
        """Process a payment notification and credit the user."""
        driver_name = SystemSetting.get('payment_driver', 'simulate')

        xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if xff:
            remote_ip = xff.split(',')[0].strip()
        else:
            remote_ip = request.META.get('REMOTE_ADDR', '')
        logger.info(
            '支付回调: ip=%s driver=%s', remote_ip, driver_name,
        )

        if driver_name == 'simulate':
            if not request.user.is_authenticated:
                return Response({'error': '需要认证'}, status=401)
            secret = request.data.get('secret', '')
            expected = hashlib.sha256(
                (settings.SECRET_KEY + 'payment_notify').encode(),
            ).hexdigest()[:16]
            if secret != expected:
                logger.warning(
                    '模拟支付回调密钥错误: ip=%s, user=%s',
                    remote_ip, request.user.id,
                )
                return Response({'error': '无效的密钥'}, status=403)

        driver = get_payment_driver(request)
        verified = driver.verify_notification(request)
        if not verified:
            logger.warning(
                '支付回调验签失败: ip=%s, driver=%s',
                remote_ip, driver_name,
            )
            return Response({'error': '验签失败'}, status=400)

        out_trade_no = verified['out_trade_no']
        trade_no = verified['trade_no']

        try:
            order = PaymentOrder.objects.get(
                out_trade_no=out_trade_no, status='pending',
            )
        except PaymentOrder.DoesNotExist:
            return Response(
                {'error': '订单不存在或已处理'}, status=400,
            )

        if driver_name == 'simulate' and order.user != request.user:
            return Response({'error': '无权操作此订单'}, status=403)

        logger.info(
            '支付回调成功: order=%s, ip=%s, driver=%s',
            out_trade_no, remote_ip, driver_name,
        )
        return self._complete(order, trade_no)

    def _complete(
        self, order: PaymentOrder, trade_no: str,
    ) -> Response:
        """Mark order paid and credit the user's wallet."""
        order.status = 'paid'
        order.trade_no = trade_no
        order.paid_at = timezone.now()
        order.save()

        Recharge.objects.create(
            user=order.user,
            amount=order.amount,
            status='completed',
            confirmed_at=order.paid_at,
            admin_remark=f'支付宝自动到账 [{trade_no}]',
        )

        wallet, _ = Wallet.objects.get_or_create(user=order.user)
        wallet.balance += order.amount
        wallet.save()

        amount_yuan = order.amount / 100
        return Response({
            'success': True,
            'message': f'已到账 ¥{amount_yuan:.2f}',
        })


class PaymentOrderListView(APIView):
    """List payment orders for the current user."""

    def get(self, request: Request) -> Response:
        """Return the user's payment orders."""
        orders = PaymentOrder.objects.filter(user=request.user)
        return Response(PaymentOrderSerializer(orders, many=True).data)


class PaymentQRPublicView(APIView):
    """Return the public QR code URL for payments."""

    permission_classes = [permissions.AllowAny]

    def get(self, request: Request) -> Response:
        """Return QR code URL if configured."""
        config = PaymentConfig.objects.first()
        if not config or not config.qr_code:
            return Response({'qr_url': None, 'has_qr': False})
        return Response({
            'qr_url': request.build_absolute_uri(config.qr_code.url),
            'has_qr': True,
        })


class PaymentQRImageView(APIView):
    """Serve the payment QR code image."""

    permission_classes = [permissions.AllowAny]

    def get(self, request: Request) -> Response:
        """Return the QR code image file."""
        config = PaymentConfig.objects.first()
        if not config or not config.qr_code:
            return Response({'error': '收款码未设置'}, status=404)
        content_type, _ = mimetypes.guess_type(config.qr_code.name)
        return FileResponse(
            config.qr_code.open('rb'),
            content_type=content_type or 'image/png',
        )


class PasswordResetRequestView(APIView):
    """Send a password reset email to the user."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = []  # set in urls.py

    def post(self, request: Request) -> Response:
        """Send a password reset link to the user's email."""
        email = request.data.get('email', '')

        cache_key = f'pwd_reset_{email}'
        if cache.get(cache_key):
            return Response(
                {'error': '请勿频繁请求，请稍后再试'},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            cache.set(cache_key, True, 60)
            return Response(
                {'error': '该邮箱未注册'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)
        reset_url = (
            f"{request.scheme}://{request.get_host()}"
            f"/reset-password?uid={uid}&token={token}"
        )

        try:
            send_mail(
                'v2man 密码重置',
                f'请点击以下链接重置密码：\n\n{reset_url}\n\n'
                f'如果您没有请求重置密码，请忽略此邮件。',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
        except Exception:
            return Response(
                {'error': '邮件发送失败，请检查邮箱配置'}, status=500,
            )

        cache.set(cache_key, True, 60)
        logger.info('密码重置请求: email=%s', email)
        return Response({
            'success': True, 'message': '重置链接已发送到您的邮箱',
        })


class PasswordResetConfirmView(APIView):
    """Confirm a password reset with token verification."""

    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> Response:
        """Reset password after verifying the reset token."""
        uid = request.data.get('uid', '')
        token = request.data.get('token', '')
        password = request.data.get('password', '')

        cache_key = f'pwd_reset_confirm_{uid}'
        attempts = cache.get(cache_key, 0)
        if attempts >= 5:
            return Response(
                {'error': '尝试次数过多，请稍后再试'},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        if not password or len(password) < 8:
            return Response(
                {'error': '密码至少8位'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            pk = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=pk)
        except (User.DoesNotExist, ValueError, TypeError):
            cache.set(cache_key, attempts + 1, 3600)
            return Response(
                {'error': '无效的链接'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not token_generator.check_token(user, token):
            cache.set(cache_key, attempts + 1, 3600)
            return Response(
                {'error': '链接已过期或无效'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cache.delete(cache_key)
        user.set_password(password)
        user.save()
        logger.info('密码重置成功: user_id=%s', user.id)
        return Response({
            'success': True, 'message': '密码已重置，请重新登录',
        })
