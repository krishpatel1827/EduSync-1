from django.urls import path
from .api_views import (
    StudentProfileAPIView,
    StudentListAPIView,
    StudentDetailAPIView,
)

app_name = 'api_student'

urlpatterns = [
    path('profile/', StudentProfileAPIView.as_view(), name='profile'),
    path('list/', StudentListAPIView.as_view(), name='list'),
    path('<str:student_id>/', StudentDetailAPIView.as_view(), name='detail'),
]
