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
    # Room management
    path('rooms/', views.room_list, name='room_list'),
    path('rooms/add/', views.room_create, name='room_create'),
    path('rooms/edit/<int:room_id>/', views.room_edit, name='room_edit'),
    path('rooms/delete/<int:room_id>/', views.room_delete, name='room_delete'),
]
