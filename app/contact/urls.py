from django.urls import path

from . import views

urlpatterns = [
    path("contact/", views.ContactMessageListCreateView.as_view(), name="contact-list"),
    path("contact/<int:pk>/reply/", views.ContactMessageReplyView.as_view(), name="contact-reply"),
    path("contact/unread-count/", views.ContactUnreadView.as_view(), name="contact-unread"),
]
