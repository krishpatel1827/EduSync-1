from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('students/', views.teacher_students, name='teacher_students'),
    path('list/', views.teacher_list, name='teacher_list'),
    path('add/', views.teacher_create, name='teacher_create'),
    path('edit/<int:teacher_id>/', views.teacher_edit, name='teacher_edit'),
    path('delete/<int:teacher_id>/', views.teacher_delete, name='teacher_delete'),
    path('attendance/generator/', views.attendance_generator, name='attendance_generator'),
    path('attendance/archives/', views.attendance_archives, name='attendance_archives'),
    path('attendance/sheet/<int:dept_id>/<str:date_from>/<str:date_to>/<int:total_lectures>/', views.attendance_sheet, name='attendance_sheet'),
    path('marks/generator/', views.generate_marks, name='generate_marks'),
    path('marks/entry/<int:dept_id>/', views.marks_entry_sheet, name='marks_entry_sheet'),
    path('account-settings/', views.teacher_account_settings, name='teacher_account_settings'),
]
