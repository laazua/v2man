from django.urls import path
from . import views

urlpatterns = [
    path('', views.PlanListView.as_view(), name='plan-list'),
    path('purchase/<int:plan_id>/', views.PurchaseView.as_view(), name='plan-purchase'),
]
