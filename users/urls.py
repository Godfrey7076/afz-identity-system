from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, VisitorViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'visitors', VisitorViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
