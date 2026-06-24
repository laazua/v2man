"""
Admin URL configuration for v2man project.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from contact.views import AdminContactViewSet
from users.admin_views import (
    AdminNodeViewSet,
    AdminPaymentQRView,
    AdminPaymentSettingsView,
    AdminPlanViewSet,
    AdminRechargeViewSet,
    AdminUserViewSet,
)

router = DefaultRouter()
router.register(r"users", AdminUserViewSet)
router.register(r"nodes", AdminNodeViewSet)
router.register(r"plans", AdminPlanViewSet)
router.register(r"recharges", AdminRechargeViewSet)
router.register(r"contact", AdminContactViewSet, basename="admin-contact")

urlpatterns = [
    path("", include(router.urls)),
    path("payment/qr/", AdminPaymentQRView.as_view(), name="admin-payment-qr"),
    path(
        "payment/settings/",
        AdminPaymentSettingsView.as_view(),
        name="admin-payment-settings",
    ),
]
