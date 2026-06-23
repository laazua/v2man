"""URL configuration for the nodes app."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.NodeListView.as_view(), name="node-list"),
]
