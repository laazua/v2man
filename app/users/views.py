from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import RegisterSerializer, UserProfileSerializer
from .models import User
from nodes.subscription import Subscription
from .wallet import Recharge


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
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





token_generator = PasswordResetTokenGenerator()


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': '该邮箱未注册'}, status=status.HTTP_400_BAD_REQUEST)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)
        reset_url = f"{request.data.get('base_url', '')}/reset-password?uid={uid}&token={token}"

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
