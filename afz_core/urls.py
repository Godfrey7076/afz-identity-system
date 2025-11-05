from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/verification/', include('identity_verification.urls')),
    path('api/users/', include('users.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('login/', TemplateView.as_view(template_name='verification/login.html'), name='login'),
    path('dashboard/', TemplateView.as_view(template_name='dashboard.html'),
         name='dashboard'),
    path('visitor-management/', TemplateView.as_view(
        template_name='visitor_management.html'), name='visitor_management'),
    path('user-management/', TemplateView.as_view(template_name='user_management.html'),
         name='user_management'),
    path('', TemplateView.as_view(
        template_name='verification/login.html'), name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
