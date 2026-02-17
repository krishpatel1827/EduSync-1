from django.contrib import admin
from .models import Timetable, Room, Division, TimeSlot, TimetableEntry

@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ['name', 'institution', 'department', 'course', 'created_by', 'status', 'created_at', 'is_active']
    list_filter = ['institution', 'department', 'is_active', 'status']
    search_fields = ['name', 'institution__name', 'department__name', 'course__name']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'institution', 'is_active', 'status')
        }),
        ('Assignment (Optional)', {
            'fields': ('department', 'course', 'created_by'),
            'description': 'Assign to specific department/course for targeted visibility. Leave blank for institution-wide timetables.'
        }),
        ('Configuration', {
            'fields': ('days_count', 'theme_palette')
        }),
        ('Headers & Footers', {
            'fields': ('heading_1', 'heading_2', 'footer_semester_text', 'footer_prepared_by', 'footer_hod'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['number', 'institution']
    list_filter = ['institution']
    search_fields = ['number']

@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = ['name', 'timetable']
    list_filter = ['timetable']
    search_fields = ['name']

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['lecture_number', 'start_time', 'end_time', 'is_break', 'timetable']
    list_filter = ['is_break', 'timetable']
    ordering = ['lecture_number']

@admin.register(TimetableEntry)
class TimetableEntryAdmin(admin.ModelAdmin):
    list_display = ['timetable', 'day', 'timeslot', 'division', 'subject', 'faculty', 'room']
    list_filter = ['day', 'timetable', 'division']
    search_fields = ['subject__name', 'faculty__user__first_name', 'faculty__user__last_name']
