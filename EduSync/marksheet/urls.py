from django.urls import path
from . import views

urlpatterns = [
    path('admin-dashboard/marksheet/', views.admin_marksheet_view, name='marksheet_admin'),
    path('teacher/enter-marks/', views.teacher_marks_entry, name='teacher_enter_marks'),
    path('my-marksheet/', views.student_my_marksheet, name='student_marksheet'),
    path('generate-bulk/', views.generate_bulk_marksheets, name='generate_bulk_marksheets'),
    path('entry-sheet/<int:dept_id>/<int:num_subjects>/<int:semester>/<str:academic_year>/', 
         views.marksheet_entry_sheet, name='marksheet_entry_sheet'),
    path('manage/', views.manage_marksheets, name='manage_marksheets'),
    path('delete-group/<int:dept_id>/<int:semester>/<str:academic_year>/', 
         views.delete_marksheet_group, name='delete_marksheet_group'),
]
