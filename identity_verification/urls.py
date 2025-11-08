# identity_verification/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'face-verification',
                views.FaceVerificationViewSet, basename='face-verification')
router.register(r'access-logs', views.AccessLogViewSet, basename='access-logs')

urlpatterns = [
    # Home and Authentication
    path('', views.home_view, name='home'),
    path('login/', views.custom_login, name='login'),
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('admin-logout/', views.admin_logout_view, name='admin_logout'),

    # Face Recognition
    path('face-login/', views.face_login_view, name='face_login'),
    path('enroll-face/', views.enroll_face_view, name='enroll_face'),
    path('face-status/', views.face_verification_status,
         name='face_verification_status'),

    # Dashboards
    path('dashboard/', views.dashboard, name='dashboard'),
    path('enhanced-dashboard/', views.EnhancedDashboardView.as_view(),
         name='enhanced_dashboard'),
    path('api/dashboard-data/',
         views.DashboardAPIView.as_view(), name='dashboard_api'),

    # User Management
    path('user-management/', views.user_management_view, name='user_management'),
    path('user/<int:user_id>/', views.user_detail_view, name='user_detail'),
    path('user/<int:user_id>/toggle-status/',
         views.toggle_user_status, name='toggle_user_status'),
    path('user/<int:user_id>/register-face/',
         views.register_user_face, name='register_user_face'),

    # Analytics and Logs
    path('access-logs-analytics/', views.access_logs_analytics,
         name='access_logs_analytics'),
    path('system-status/', views.system_status_view, name='system_status'),
    path('security-audit/', views.security_audit_view, name='security_audit'),

    # API Routes
    path('api/', include(router.urls)),
]

# Error handlers
handler404 = 'identity_verification.views.handler404'
handler500 = 'identity_verification.views.handler500'
handler403 = 'identity_verification.views.handler403'
handler400 = 'identity_verification.views.handler400'
