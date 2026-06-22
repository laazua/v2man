import logging
from rest_framework import viewsets, mixins, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.conf import settings

from .models import User
from .wallet import Wallet, Recharge, PaymentConfig
from .serializers import UserProfileSerializer, RechargeSerializer
from .permissions import IsAdminUser
from nodes.models import Node
from nodes.serializers import NodeSerializer
from nodes.subscription import Subscription
from nodes.ssh_utils import deploy_v2ray
from plans.models import Plan
from plans.serializers import PlanSerializer
from invite.models import Referral, SystemSetting

logger = logging.getLogger('business')


class AdminUserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all().select_related('plan', 'wallet')
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAdminUser]

    @action(detail=True, methods=['patch'])
    def update_user(self, request, pk=None):
        user = self.get_object()
        plan_id = request.data.get('plan_id')
        traffic_used = request.data.get('traffic_used')
        traffic_total = request.data.get('traffic_total')
        is_active = request.data.get('is_active')
        expire_date = request.data.get('expire_date')
        email = request.data.get('email')
        password = request.data.get('password')

        if plan_id is not None:
            if str(plan_id) in ("0", "", "null"):
                user.plan = None
            else:
                try:
                    user.plan = Plan.objects.get(id=int(plan_id))
                except (Plan.DoesNotExist, ValueError, TypeError):
                    return Response({'error': '套餐不存在'}, status=400)
        if traffic_used is not None:
            try:
                user.traffic_used = int(traffic_used)
            except (ValueError, TypeError):
                return Response({'error': 'traffic_used 必须为数字'}, status=400)
        if traffic_total is not None:
            try:
                user.traffic_total = int(traffic_total)
            except (ValueError, TypeError):
                return Response({'error': 'traffic_total 必须为数字'}, status=400)
        if is_active is not None:
            if isinstance(is_active, bool):
                user.is_active = is_active
            elif isinstance(is_active, str):
                user.is_active = is_active.lower() in ('true', '1', 'yes')
            else:
                user.is_active = bool(is_active)
        if expire_date is not None:
            user.expire_date = expire_date
        if email is not None:
            user.email = email
        if password:
            user.set_password(password)
        user.save()

        # 如果修改了影响节点配置的字段，同步到节点
        sync_results = None
        if any(k in request.data for k in ("plan_id", "is_active", "expire_date")):
            from nodes.ssh_utils import sync_users_to_node
            sync_results = []
            for node in Node.objects.filter(is_active=True):
                err = sync_users_to_node(node)
                sync_results.append({"node": node.name, "success": err is None, "error": err or ""})

        data = UserProfileSerializer(user).data
        if sync_results:
            data["sync_results"] = sync_results
        logger.info('管理员更新用户: admin_id=%s target_user_id=%s fields=%s',
                     request.user.id, user.id, list(request.data.keys()))
        return Response(data)

    @action(detail=True, methods=['post'])
    def top_up(self, request, pk=None):
        user = self.get_object()
        amount = request.data.get('amount', 0)
        try:
            amount = int(amount)
        except (ValueError, TypeError):
            return Response({'error': '金额必须为整数'}, status=400)
        if amount < 1:
            return Response({'error': '金额必须大于0'}, status=400)
        wallet, _ = Wallet.objects.get_or_create(user=user)
        wallet.balance += amount
        wallet.save()
        logger.info('管理员手动充值: admin_id=%s target_user_id=%s amount=%s',
                     request.user.id, user.id, amount)
        return Response({
            'success': True,
            'message': f'已为 {user.username} 充值 ¥{amount/100:.2f}',
            'balance': wallet.balance,
        })

    @action(detail=True, methods=['post'])
    def invalidate_subscription(self, request, pk=None):
        import uuid
        user = self.get_object()
        new_uuid = uuid.uuid4()
        user.uuid = new_uuid
        user.save()
        try:
            sub = Subscription.objects.get(user=user)
            sub.delete()
        except Subscription.DoesNotExist:
            pass

        sync_errors = []
        if user.plan:
            from nodes.ssh_utils import sync_users_to_node
            for node in user.plan.nodes.filter(is_active=True):
                err = sync_users_to_node(node)
                if err:
                    sync_errors.append({"node": node.name, "error": err})

        logger.info('管理员重置订阅: admin_id=%s target_user_id=%s new_uuid=%s',
                     request.user.id, user.id, new_uuid)
        return Response({
            'success': True,
            'message': f'订阅已失效，用户 {user.username} 的新 UUID 已同步到节点',
            'new_uuid': str(new_uuid),
            'sync_errors': sync_errors if sync_errors else None,
        })

    @action(detail=True, methods=['post'])
    def sync_config(self, request, pk=None):
        user = self.get_object()
        sync_results = []
        if user.plan:
            from nodes.ssh_utils import sync_users_to_node
            for node in user.plan.nodes.filter(is_active=True):
                err = sync_users_to_node(node)
                sync_results.append({
                    "node": node.name,
                    "success": err is None,
                    "error": err or "",
                })
        logger.info('管理员同步节点配置: admin_id=%s target_user_id=%s',
                     request.user.id, user.id)
        return Response({
            'success': True,
            'message': f'已向 {user.username} 关联的节点推送配置',
            'sync_results': sync_results,
        })


class AdminNodeViewSet(viewsets.ModelViewSet):
    queryset = Node.objects.all()
    serializer_class = NodeSerializer
    permission_classes = [permissions.IsAdminUser]

    @action(detail=True, methods=['post'])
    def deploy(self, request, pk=None):
        node = self.get_object()
        if not node.ssh_key and not node.ssh_password:
            return Response({'success': False, 'error': f'节点 {node.name} 未配置 SSH 私钥或密码'}, status=400)
        r = deploy_v2ray(node)
        logger.info('管理员部署节点: admin_id=%s node_id=%s node_name=%s success=%s',
                     request.user.id, node.id, node.name, r.get('success'))
        return Response(r)


class AdminPlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [permissions.IsAdminUser]


class AdminRechargeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Recharge.objects.all().select_related('user')
    serializer_class = RechargeSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        qs = super().get_queryset()
        user_id = self.request.query_params.get('user_id')
        username = self.request.query_params.get('username')
        if user_id:
            qs = qs.filter(user_id=user_id)
        if username:
            qs = qs.filter(user__username__icontains=username)
        return qs

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        recharge = self.get_object()
        if recharge.status != 'pending':
            return Response({'error': '该充值已处理'}, status=400)
        recharge.status = 'completed'
        recharge.confirmed_at = timezone.now()
        recharge.save()
        wallet, _ = Wallet.objects.get_or_create(user=recharge.user)
        wallet.balance += recharge.amount
        wallet.save()

        try:
            ref = Referral.objects.get(invited=recharge.user)
            pct = int(SystemSetting.get('referral_percentage', '20'))
            credit = recharge.amount * pct // 100
            if credit > 0:
                inviter_wallet, _ = Wallet.objects.get_or_create(user=ref.inviter)
                inviter_wallet.balance += credit
                inviter_wallet.save()
                ref.earned += credit
                ref.save()
        except Referral.DoesNotExist:
            pass

        logger.info('管理员确认充值: admin_id=%s recharge_id=%s user_id=%s amount=%s',
                     request.user.id, recharge.id, recharge.user_id, recharge.amount)
        return Response({'success': True, 'message': f'已确认 ¥{recharge.amount/100:.2f} 充值'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        recharge = self.get_object()
        if recharge.status != 'pending':
            return Response({'error': '该充值已处理'}, status=400)
        recharge.status = 'failed'
        recharge.admin_remark = request.data.get('remark', '管理员拒绝')
        recharge.save()
        logger.info('管理员拒绝充值: admin_id=%s recharge_id=%s user_id=%s',
                     request.user.id, recharge.id, recharge.user_id)
        return Response({'success': True, 'message': '已拒绝充值'})


class AdminPaymentQRView(APIView):
    permission_classes = [permissions.IsAdminUser]
    MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB
    ALLOWED_CONTENT_TYPES = {
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
    }

    def get(self, request):
        config = PaymentConfig.objects.first()
        if not config or not config.qr_code:
            return Response({'qr_url': None})
        return Response({'qr_url': request.build_absolute_uri(config.qr_code.url)})

    def post(self, request):
        file = request.FILES.get('qr_code')
        if not file:
            return Response({'error': '请上传图片'}, status=400)

        if file.content_type not in self.ALLOWED_CONTENT_TYPES:
            return Response({'error': '仅支持 JPEG/PNG/GIF/WebP 格式'}, status=400)

        if file.size > self.MAX_FILE_SIZE:
            return Response({'error': '图片大小不能超过 2MB'}, status=400)

        config = PaymentConfig.objects.first()
        if not config:
            config = PaymentConfig()
        config.qr_code = file
        config.save()
        logger.info('管理员更新收款码: admin_id=%s', request.user.id)
        return Response({
            'success': True,
            'qr_url': request.build_absolute_uri(config.qr_code.url),
            'message': '收款码已更新',
        })


class AdminPaymentSettingsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        return Response({
            'recharge_mode': SystemSetting.get('recharge_mode', 'manual'),
            'payment_driver': SystemSetting.get('payment_driver', 'simulate'),
            'alipay_app_id': SystemSetting.get('alipay_app_id', ''),
            'alipay_private_key': SystemSetting.get('alipay_private_key', ''),
            'alipay_public_key': SystemSetting.get('alipay_public_key', ''),
            'notify_url': request.build_absolute_uri('/api/auth/payment/notify/'),
        })

    def post(self, request):
        recharge_mode = request.data.get('recharge_mode', 'manual')
        payment_driver = request.data.get('payment_driver', 'simulate')

        if recharge_mode not in ('manual', 'auto'):
            return Response({'error': '无效充值模式'}, status=400)
        if payment_driver not in ('simulate', 'alipay'):
            return Response({'error': '无效支付驱动'}, status=400)

        if recharge_mode == 'auto' and payment_driver == 'alipay':
            app_id = request.data.get('alipay_app_id', '')
            private_key = request.data.get('alipay_private_key', '')
            public_key = request.data.get('alipay_public_key', '')
            if not app_id:
                return Response({'error': '启用支付宝驱动请输入 APPID'}, status=400)
            if not private_key or 'BEGIN RSA PRIVATE KEY' not in private_key:
                return Response({'error': '应用私钥格式错误，需包含 -----BEGIN RSA PRIVATE KEY-----'}, status=400)
            if not public_key or 'BEGIN PUBLIC KEY' not in public_key:
                return Response({'error': '支付宝公钥格式错误，需包含 -----BEGIN PUBLIC KEY-----'}, status=400)

        valid_keys = {
            'recharge_mode', 'payment_driver', 'alipay_app_id',
            'alipay_private_key', 'alipay_public_key',
        }
        for key, value in request.data.items():
            if key not in valid_keys:
                continue
            SystemSetting.objects.update_or_create(key=key, defaults={'value': str(value)})

        logger.info('管理员更新支付设置: admin_id=%s', request.user.id)
        return Response({'success': True})
