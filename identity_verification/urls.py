from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import (
    FaceVerificationViewSet,
    AccessLogViewSet,
    admin_face_registration,
    face_login_view,
    face_verification_status
)

# Initialize router
router = DefaultRouter()
router.register(r'verification', FaceVerificationViewSet,
                basename='verification')
router.register(r'access-logs', AccessLogViewSet)

# URL patterns
urlpatterns = [
    # API routes
    path('api/', include(router.urls)),

    # Admin face registration
    path('admin/register-face/<int:user_id>/',
         admin_face_registration, name='admin_face_registration'),

    # Face login interface (main entry point)
    path('login/', face_login_view, name='face_login'),

    # Status check endpoint
    path('status/', face_verification_status, name='face_verification_status'),

    # Additional utility endpoints can be added here
]

# Optional: Add API info endpoint
urlpatterns += [
    path('api/info/', views.api_info, name='api_info'),
]
