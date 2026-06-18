from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import RegisterSerializer, UserProfileSerializer
from .models import User
from nodes.subscription import Subscription
from .wallet import Recharge, PaymentConfig
from invite.models import InviteCode, Referral


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        code_str = serializer.validated_data.get('invite_code', '')
        if code_str:
            try:
                code = InviteCode.objects.get(code=code_str, is_active=True)
                if code.owner != user:
                    Referral.objects.create(inviter=code.owner, invited=user, invite_code=code)
            except InviteCode.DoesNotExist:
                pass

        return Response({
            'user': UserProfileSerializer(user).data,
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

    def patch(self, request):
        user = request.user
        email = request.data.get('email')
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if email is not None:
            user.email = email
        if new_password:
            if not old_password or not user.check_password(old_password):
                return Response({'error': '原密码不正确'}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(new_password)
        user.save()
        return Response(UserProfileSerializer(user).data)


class RechargeView(APIView):
    def post(self, request):
        amount = request.data.get('amount', 0)
        try:
            amount = int(amount)
        except (ValueError, TypeError):
            return Response({'error': '无效金额'}, status=status.HTTP_400_BAD_REQUEST)
        if amount < 1:
            return Response({'error': '金额必须大于0'}, status=status.HTTP_400_BAD_REQUEST)
        Recharge.objects.create(user=request.user, amount=amount)
        return Response({'success': True, 'message': '充值已提交，等待管理员确认'})


class PaymentQRPublicView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        config = PaymentConfig.objects.first()
        if not config or not config.qr_code:
            return Response({'qr_url': None, 'has_qr': False})
        return Response({'qr_url': request.build_absolute_uri(config.qr_code.url), 'has_qr': True})


class PaymentQRImageView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from django.http import FileResponse
        import mimetypes
        config = PaymentConfig.objects.first()
        if not config or not config.qr_code:
            return Response({'error': '收款码未设置'}, status=404)
        content_type, _ = mimetypes.guess_type(config.qr_code.name)
        return FileResponse(config.qr_code.open('rb'), content_type=content_type or 'image/png')





token_generator = PasswordResetTokenGenerator()


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '')

        cache_key = f'pwd_reset_{email}'
        if cache.get(cache_key):
            return Response({'error': '请勿频繁请求，请稍后再试'}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            cache.set(cache_key, True, 60)
            return Response({'error': '该邮箱未注册'}, status=status.HTTP_400_BAD_REQUEST)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)
        reset_url = f"{request.scheme}://{request.get_host()}/reset-password?uid={uid}&token={token}"

        try:
            send_mail(
                'v2man 密码重置',
                f'请点击以下链接重置密码：\n\n{reset_url}\n\n如果您没有请求重置密码，请忽略此邮件。',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
        except Exception:
            return Response({'error': '邮件发送失败，请检查邮箱配置'}, status=500)

        cache.set(cache_key, True, 60)
        return Response({'success': True, 'message': '重置链接已发送到您的邮箱'})


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        uid = request.data.get('uid', '')
        token = request.data.get('token', '')
        password = request.data.get('password', '')

        if not password or len(password) < 6:
            return Response({'error': '密码至少6位'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            pk = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=pk)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({'error': '无效的链接'}, status=status.HTTP_400_BAD_REQUEST)

        if not token_generator.check_token(user, token):
            return Response({'error': '链接已过期或无效'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password)
        user.save()
        return Response({'success': True, 'message': '密码已重置，请重新登录'})
