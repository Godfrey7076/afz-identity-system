"""
URL configuration for afz_core project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Admin Site
    path('admin/', admin.site.urls),

    # Identity Verification System - Main Application
    path('verification/', include('identity_verification.urls')),

    # API Routes
    path('api/verification/', include('identity_verification.urls')),

    # Root redirect to enhanced dashboard
    path('', RedirectView.as_view(
        url='/verification/enhanced-dashboard/', permanent=False), name='home'),

    # Legacy dashboard redirect
    path('dashboard/', RedirectView.as_view(url='/verification/enhanced-dashboard/', permanent=False)),
]

# Admin site customization
admin.site.site_header = 'AFZ Identity System Administration'
admin.site.site_title = 'AFZ Identity System'
admin.site.index_title = 'System Administration'

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
