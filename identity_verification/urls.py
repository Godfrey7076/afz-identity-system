from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import (
    FaceVerificationViewSet,
    AccessLogViewSet,
    admin_face_registration,
    face_login_view,
    face_verification_status,
    api_info,
    DashboardView,
    user_management_view,
    visitor_management_view,
    admin_login_view,
    admin_logout_view
)

# Initialize router
router = DefaultRouter()
router.register(r'verification', FaceVerificationViewSet,
                basename='verification')
router.register(r'access-logs', AccessLogViewSet)

# URL patterns
urlpatterns = [
    # Authentication routes
    path('admin-login/', admin_login_view, name='admin_login'),
    path('admin-logout/', admin_logout_view, name='admin_logout'),

    # API routes
    path('api/', include(router.urls)),

    # Admin face registration
    path('admin/register-face/<int:user_id>/',
         admin_face_registration, name='admin_face_registration'),

    # Face login interface (for users)
    path('login/', face_login_view, name='face_login'),

    # Status check endpoint
    path('status/', face_verification_status, name='face_verification_status'),

    # Dashboard URLs (protected)
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('user-management/', user_management_view, name='user_management'),
    path('visitor-management/', visitor_management_view, name='visitor_management'),

    # API info endpoint
    path('api/info/', api_info, name='api_info'),
]
