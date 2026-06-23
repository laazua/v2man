"""
URL configuration for v2man project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns: list = [
    path('api/auth/', include('users.urls')),
    path('api/nodes/', include('nodes.urls')),
    path('api/subscription/', include('nodes.urls_sub')),
    path('api/plans/', include('plans.urls')),
    path('api/traffic/', include('traffic.urls')),
    path('api/admin/', include('config.admin_urls')),
    path('api/', include('invite.urls')),
    path('api/', include('notify.urls')),
    path('api/', include('contact.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
