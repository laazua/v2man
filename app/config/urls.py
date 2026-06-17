from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/nodes/', include('nodes.urls')),
    path('api/subscription/', include('nodes.urls_sub')),
    path('api/plans/', include('plans.urls')),
    path('api/traffic/', include('traffic.urls')),
    path('api/admin/', include('config.admin_urls')),
]
