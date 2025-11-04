from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FaceVerificationViewSet, AccessLogViewSet

router = DefaultRouter()
router.register(r'verification', FaceVerificationViewSet,
                basename='verification')
router.register(r'access-logs', AccessLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
