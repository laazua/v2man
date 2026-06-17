from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.admin_views import AdminUserViewSet, AdminNodeViewSet, AdminPlanViewSet, AdminRechargeViewSet

router = DefaultRouter()
router.register(r'users', AdminUserViewSet)
router.register(r'nodes', AdminNodeViewSet)
router.register(r'plans', AdminPlanViewSet)
router.register(r'recharges', AdminRechargeViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
