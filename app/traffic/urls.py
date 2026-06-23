"""URL configuration for the traffic module."""

from django.urls import path

from . import views

urlpatterns = [
    path('record/', views.TrafficRecordView.as_view(), name='traffic-record'),
    path('stats/', views.TrafficStatsView.as_view(), name='traffic-stats'),
]
