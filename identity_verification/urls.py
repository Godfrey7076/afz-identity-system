# identity_verification/urls.py
from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from django.urls import path
from . import views

# Initialize router
router = DefaultRouter()
router.register(r'api/face-verification',
                views.FaceVerificationViewSet, basename='face-verification')
router.register(r'api/access-logs', views.AccessLogViewSet,
                basename='access-logs')

urlpatterns = [
    path('safe-start-camera/', views.safe_start_camera, name='safe_start_camera'),
    path('safe-face-recognition/', views.safe_face_recognition,
         name='safe_face_recognition'),
    path('stop-cameras/', views.stop_all_cameras, name='stop_all_cameras'),
    path('camera-status/', views.camera_status, name='camera_status'),
    # Home and Authentication
    path('', views.home_view, name='home'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('admin-logout/', views.admin_logout_view, name='admin_logout'),

    # Face Recognition
    # ADDED: Missing URL for Identity Verification
    path('verify/', views.face_login_view, name='verify_identity'),
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

    # Analytics and System
    path('access-logs-analytics/', views.access_logs_analytics,
         name='access_logs_analytics'),
    path('system-status/', views.system_status_view, name='system_status'),
    path('security-audit/', views.security_audit_view, name='security_audit'),

    # Camera management URLs
    path('video_feed/<int:camera_id>/', views.video_feed, name='video_feed'),
    path('start_camera/', views.start_camera, name='start_camera'),
    path('stop_camera/', views.stop_camera, name='stop_camera'),
    path('camera_status/', views.camera_status, name='camera_status'),
    path('available_cameras/', views.get_available_cameras,
         name='available_cameras'),
    path('stop_all_cameras/', views.stop_all_cameras, name='stop_all_cameras'),
    path('capture_face/', views.capture_face, name='capture_face'),

    # ADD THIS NEW URL
    path('test_camera/', views.test_camera, name='test_camera'),



    # API Routes
    path('api/', include(router.urls)),

    # Media and Static files
    path('media/<path:path>', views.serve_media, name='serve_media'),
    path('static/<path:path>', views.serve_static, name='serve_static'),
]

# Error handlers
handler404 = 'identity_verification.views.handler404'
handler500 = 'identity_verification.views.handler500'
handler403 = 'identity_verification.views.handler403'
handler400 = 'identity_verification.views.handler400'
