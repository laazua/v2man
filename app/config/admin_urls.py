from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.admin_views import AdminUserViewSet, AdminNodeViewSet, AdminPlanViewSet, AdminRechargeViewSet, AdminPaymentQRView
from contact.views import AdminContactViewSet

router = DefaultRouter()
router.register(r'users', AdminUserViewSet)
router.register(r'nodes', AdminNodeViewSet)
router.register(r'plans', AdminPlanViewSet)
router.register(r'recharges', AdminRechargeViewSet)
router.register(r'contact', AdminContactViewSet, basename='admin-contact')

urlpatterns = [
    path('', include(router.urls)),
    path('payment/qr/', AdminPaymentQRView.as_view(), name='admin-payment-qr'),
]
