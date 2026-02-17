from django.urls import path
from . import views

urlpatterns = [
    path('portal/login/teacher/', views.teacher_portal_login, name='teacher_portal_login'),
    path('portal/login/student/', views.student_portal_login, name='student_portal_login'),
    # path('dashboard/', views.dashboard_view, name='dashboard'),
    path('admin/dashboard/', views.institution_admin_dashboard, name='institution_admin_dashboard'),
    path('news/delete/<int:news_id>/', views.delete_news, name='delete_news'),
    path('departments/', views.department_list, name='department_list'),
    path('departments/delete/<int:dept_id>/', views.delete_department, name='delete_department'),
]
