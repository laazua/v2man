from django.urls import path
from . import views

urlpatterns = [
    path('notifications/', views.NotificationListView.as_view()),
    path('notifications/unread-count/', views.UnreadCountView.as_view()),
    path('notifications/mark-read/', views.MarkReadView.as_view()),
    path('admin/notifications/', views.AdminNotificationListCreateView.as_view()),
    path('admin/notifications/<int:pk>/', views.AdminNotificationDetailView.as_view()),
]
