from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('timetable-generator/', views.dashboard, name='generator'),
    path('timetable/', views.timetable_view, name='timetable'),
    path('timetable/<int:timetable_id>/', views.timetable_view, name='timetable'),
    path('history/', views.history, name='history'),
    path('add/', views.add_entry, name='add_entry'),
    path('setup/', views.setup_view, name='setup'),
    path('export/excel/<int:timetable_id>/', views.export_excel, name='export_excel'),
    path('history/delete/<int:timetable_id>/', views.history_delete, name='history_delete'),
    path('export/pdf/<int:timetable_id>/', views.export_pdf, name='export_pdf'),
    path('auto-generate/<int:timetable_id>/', views.auto_generate_timetable, name='auto_generate_timetable'),
    path('clear/<int:timetable_id>/', views.clear_timetable_entries, name='clear_timetable'),
    path('edit-header/<int:timetable_id>/', views.edit_timetable_header, name='edit_timetable_header'),
    path('toggle-theme/<int:timetable_id>/', views.toggle_theme, name='toggle_theme'),
    path('publish/<int:timetable_id>/', views.publish_timetable, name='publish_timetable'),
    path('api/branches/', views.api_branches, name='api_branches'),
]
