from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'verification', views.FaceVerificationViewSet,
                basename='verification')
router.register(r'access-logs', views.AccessLogViewSet)

urlpatterns = [
    # API Routes
    path('api/', include(router.urls)),

    # Enhanced Dashboard Routes
    path('enhanced-dashboard/', views.EnhancedDashboardView.as_view(),
         name='enhanced_dashboard'),
    path('api/dashboard/', views.DashboardAPIView.as_view(), name='dashboard_api'),

    # Authentication Routes
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('logout/', views.admin_logout_view, name='admin_logout'),

    # User Management Routes
    path('user-management/', views.user_management_view, name='user_management'),
    path('user-detail/<int:user_id>/',
         views.user_detail_view, name='user_detail'),
    path('toggle-user-status/<int:user_id>/',
         views.toggle_user_status, name='toggle_user_status'),
    path('register-user-face/<int:user_id>/',
         views.register_user_face, name='register_user_face'),

    # Visitor Management Routes
    path('visitor-management/', views.visitor_management_view,
         name='visitor_management'),

    # Security & System Routes
    path('security-audit/', views.security_audit_view, name='security_audit'),
    path('system-status/', views.system_status_view, name='system_status'),

    # Face Verification Routes
    path('login/', views.face_login_view, name='face_login'),
    path('face-status/', views.face_verification_status, name='face_status'),
    path('admin/register-face/<int:user_id>/',
         views.admin_face_registration, name='admin_face_registration'),

    # Legacy Dashboard (keep for compatibility)
    path('dashboard/', views.EnhancedDashboardView.as_view(), name='dashboard'),

    # System Info
    path('api-info/', views.api_info, name='api_info'),
]
