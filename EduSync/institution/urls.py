from django.urls import path
from . import views

urlpatterns = [
    # path('dashboard/', views.dashboard_view, name='dashboard'),
    path('admin/dashboard/', views.institution_admin_dashboard, name='institution_admin_dashboard'),
    path('news/delete/<int:news_id>/', views.delete_news, name='delete_news'),
    path('departments/', views.department_list, name='department_list'),
    path('departments/delete/<int:dept_id>/', views.delete_department, name='delete_department'),
]
