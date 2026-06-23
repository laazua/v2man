"""URL routing for the users app authentication and payment endpoints."""

from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from . import views
from .throttles import (
    LoginThrottle,
    PasswordResetThrottle,
    RegisterThrottle,
)

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(
        throttle_classes=[LoginThrottle],
    ), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='refresh'),
    path('register/', views.RegisterView.as_view(
        throttle_classes=[RegisterThrottle],
    ), name='register'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('recharge/', views.RechargeView.as_view(), name='recharge'),
    path('password-reset/', views.PasswordResetRequestView.as_view(
        throttle_classes=[PasswordResetThrottle],
    ), name='password-reset'),
    path('password-reset/confirm/', views.PasswordResetConfirmView.as_view(
        throttle_classes=[PasswordResetThrottle],
    ), name='password-reset-confirm'),
    path('payment/qr/', views.PaymentQRPublicView.as_view(),
         name='payment-qr'),
    path('payment/qr-image/', views.PaymentQRImageView.as_view(),
         name='payment-qr-image'),
    path('payment/mode/', views.PaymentModeView.as_view(),
         name='payment-mode'),
    path('payment/create/', views.PaymentCreateView.as_view(),
         name='payment-create'),
    path('payment/notify/', views.PaymentNotifyView.as_view(),
         name='payment-notify'),
    path('payment/orders/', views.PaymentOrderListView.as_view(),
         name='payment-orders'),
]
