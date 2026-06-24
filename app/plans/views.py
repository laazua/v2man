"""Views for plan listing and purchase."""

import logging

from django.db import transaction
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from nodes.subscription import Subscription
from users.wallet import Wallet

from .models import Plan
from .serializers import PlanSerializer

logger = logging.getLogger("business")


class PlanListView(generics.ListAPIView):
    """Public endpoint listing all active plans."""

    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]


class PurchaseView(APIView):
    """Authenticated endpoint for purchasing a plan with balance."""

    def post(self, request: Request, plan_id: int) -> Response:
        """Process plan purchase and sync nodes."""
        try:
            plan = Plan.objects.get(id=plan_id, is_active=True)
        except Plan.DoesNotExist:
            return Response(
                {"error": "套餐不存在"}, status=status.HTTP_404_NOT_FOUND
            )

        user = request.user
        is_admin = user.is_staff

        with transaction.atomic():
            wallet = None
            if not is_admin:
                wallet = Wallet.objects.select_for_update().get(user=user)
                price_cents = int(plan.price * 100)

                if wallet.balance < price_cents:
                    return Response(
                        {
                            "error": "余额不足",
                            "balance": wallet.balance,
                            "need": price_cents,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                wallet.balance -= price_cents
                wallet.save()

            user.plan = plan
            user.traffic_total = (
                plan.traffic_limit if plan.traffic_limit > 0 else -1
            )
            user.expire_date = timezone.now() + timezone.timedelta(
                days=plan.duration_days
            )
            user.save()

            sub, created = Subscription.objects.get_or_create(user=user)

            sync_errors = []
            try:
                from nodes.ssh_utils import sync_users_to_node

                for node in plan.nodes.filter(is_active=True):
                    err = sync_users_to_node(node)
                    if err:
                        sync_errors.append(f"{node.name}: {err}")
            except Exception as exc:
                sync_errors.append(str(exc))

            if sync_errors and not is_admin:
                wallet.balance += price_cents
                wallet.save()
                user.plan = None
                user.traffic_total = 0
                user.expire_date = None
                user.save()
                sub.delete()
                return Response(
                    {
                        "error": "节点同步失败，已自动退款",
                        "sync_errors": sync_errors,
                    },
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        logger.info(
            "用户购买套餐: user_id=%s plan_id=%s plan_name=%s "
            "price=%s balance_remaining=%s",
            user.id,
            plan.id,
            plan.name,
            plan.price,
            wallet.balance if wallet else 0,
        )
        return Response(
            {
                "success": True,
                "message": f"已购买 {plan.name}",
                "balance_remaining": wallet.balance if wallet else 0,
                "subscription_token": str(sub.token),
            }
        )
