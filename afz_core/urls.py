from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('verification/', include('identity_verification.urls')),
    path('', TemplateView.as_view(template_name='base.html'), name='home'),
]

# Custom admin site titles
admin.site.site_header = "🛡️ Air Force Zimbabwe - Identity System Administration"
admin.site.site_title = "AFZ Identity System"
admin.site.index_title = "Welcome to Air Force Zimbabwe Command Portal"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
