from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from .models import Plan
from .serializers import PlanSerializer
from nodes.subscription import Subscription
from users.wallet import Wallet


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

        user = request.user
        is_admin = user.is_staff

        with transaction.atomic():
            wallet = None
            if not is_admin:
                wallet = Wallet.objects.select_for_update().get(user=user)
                price_cents = int(plan.price * 100)

                if wallet.balance < price_cents:
                    return Response({
                        'error': '余额不足',
                        'balance': wallet.balance,
                        'need': price_cents,
                    }, status=status.HTTP_400_BAD_REQUEST)

                wallet.balance -= price_cents
                wallet.save()

            user.plan = plan
            user.traffic_used = 0
            user.traffic_total = plan.traffic_limit if plan.traffic_limit > 0 else 0
            user.expire_date = timezone.now() + timezone.timedelta(days=plan.duration_days)
            user.save()

            Subscription.objects.filter(user=user).delete()
            sub = Subscription.objects.create(user=user)

        return Response({
            'success': True,
            'message': f'已购买 {plan.name}',
            'balance_remaining': wallet.balance if wallet else 0,
            'subscription_token': str(sub.token),
        })
