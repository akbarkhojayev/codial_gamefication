from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    HealthCheckView,
    AnalyticsAPIView,
    SearchAPIView,
    StudentAnalyticsView,
    CourseAnalyticsView,
    GroupAnalyticsView,
    QueryLogViewSet
)

router = DefaultRouter()
router.register(r'logs', QueryLogViewSet, basename='querylog')

urlpatterns = [
    path('', include(router.urls)),
    path('health/', HealthCheckView.as_view(), name='ai-health'),
    path('analytics/', AnalyticsAPIView.as_view(), name='ai-analytics'),
    path('search/', SearchAPIView.as_view(), name='ai-search'),
    path('students/', StudentAnalyticsView.as_view(), name='students-analytics'),
    path('courses/', CourseAnalyticsView.as_view(), name='courses-analytics'),
    path('groups/', GroupAnalyticsView.as_view(), name='groups-analytics'),
]
