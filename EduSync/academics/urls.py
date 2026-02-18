from django.urls import path
from . import views

urlpatterns = [
    path('courses/', views.course_list, name='course_list'),
    path('courses/add/', views.course_create, name='course_create'),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('courses/<int:course_id>/edit/', views.course_edit, name='course_edit'),
    path('courses/<int:course_id>/delete/', views.course_delete, name='course_delete'),

    path('calendar/', views.academic_calendar_list, name='academic_calendar_list'),
    path('calendar/create/', views.academic_calendar_create, name='academic_calendar_create'),
    path('calendar/<int:calendar_id>/', views.academic_calendar_detail, name='academic_calendar_detail'),
    path('calendar/<int:calendar_id>/edit/', views.academic_calendar_edit, name='academic_calendar_edit'),
    path('calendar/<int:calendar_id>/delete/', views.academic_calendar_delete, name='academic_calendar_delete'),

    path('calendar/<int:calendar_id>/events/add/', views.calendar_event_create, name='calendar_event_create'),
    path('calendar/events/<int:event_id>/edit/', views.calendar_event_edit, name='calendar_event_edit'),
    path('calendar/events/<int:event_id>/delete/', views.calendar_event_delete, name='calendar_event_delete'),

    path('calendar/<int:calendar_id>/share/', views.academic_calendar_share, name='academic_calendar_share'),
]
