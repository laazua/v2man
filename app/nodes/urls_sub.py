from django.urls import path
from . import views_sub

urlpatterns = [
    path('<str:token>/', views_sub.SubscriptionView.as_view(), name='subscription'),
    path('<str:token>/clashmeta/', views_sub.SubscriptionView.as_view(), {'output_fmt': 'clash'}, name='subscription-clash'),
    path('<str:token>/singbox/', views_sub.SubscriptionView.as_view(), {'output_fmt': 'singbox'}, name='subscription-singbox'),
]
