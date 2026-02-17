from django.urls import path
from .api_views import (
    TeacherProfileAPIView,
    TeacherListAPIView,
    TeacherDetailAPIView,
)

app_name = 'api_teacher'

urlpatterns = [
    path('profile/', TeacherProfileAPIView.as_view(), name='profile'),
    path('list/', TeacherListAPIView.as_view(), name='list'),
    path('<str:employee_id>/', TeacherDetailAPIView.as_view(), name='detail'),
]
