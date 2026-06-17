from rest_framework import viewsets, mixins, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

from .models import User
from .wallet import Wallet, Recharge
from .serializers import UserProfileSerializer, RechargeSerializer
from .permissions import IsAdminUser
from nodes.models import Node
from nodes.serializers import NodeSerializer
from plans.models import Plan
from plans.serializers import PlanSerializer


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
            try:
                user.plan = Plan.objects.get(id=plan_id)
            except Plan.DoesNotExist:
                return Response({'error': '套餐不存在'}, status=400)
        if traffic_used is not None:
            user.traffic_used = int(traffic_used)
        if traffic_total is not None:
            user.traffic_total = int(traffic_total)
        if is_active is not None:
            user.is_active = bool(is_active)
        if expire_date is not None:
            user.expire_date = expire_date
        if email is not None:
            user.email = email
        if password:
            user.set_password(password)
        user.save()
        return Response(UserProfileSerializer(user).data)


class AdminNodeViewSet(viewsets.ModelViewSet):
    queryset = Node.objects.all()
    serializer_class = NodeSerializer
    permission_classes = [permissions.IsAdminUser]


class AdminPlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [permissions.IsAdminUser]


class AdminRechargeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Recharge.objects.all().select_related('user')
    serializer_class = RechargeSerializer
    permission_classes = [permissions.IsAdminUser]

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
        return Response({'success': True, 'message': f'已确认 ¥{recharge.amount/100:.2f} 充值'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        recharge = self.get_object()
        if recharge.status != 'pending':
            return Response({'error': '该充值已处理'}, status=400)
        recharge.status = 'failed'
        recharge.admin_remark = request.data.get('remark', '管理员拒绝')
        recharge.save()
        return Response({'success': True, 'message': '已拒绝充值'})
