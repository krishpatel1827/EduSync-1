from django.contrib import admin
from .models import Course, Grade, AttendanceSheet, Attendance, Branch, AcademicCalendar, CalendarEvent, EventTypeColor


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        'code', 'name',
        'institution', 'credits'
    )
    list_filter = (
        'institution',
    )
    search_fields = (
        'code', 'name'
    )
    filter_horizontal = (
        'teachers',
    )


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = (
        'student', 'course',
        'grade', 'marks'
    )
    list_filter = (
        'grade', 'course'
    )
    search_fields = (
        'student__user__username',
        'course__code'
    )


@admin.register(AttendanceSheet)
class AttendanceSheetAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'department', 'date_from', 'date_to', 'total_lectures', 'shared_with_students')
    list_filter = ('shared_with_students', 'department')


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'sheet', 'lectures_attended', 'total_lectures')
    list_filter = ('sheet',)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'institution')
    list_filter = ('institution', 'department')
    search_fields = ('name',)


@admin.register(AcademicCalendar)
class AcademicCalendarAdmin(admin.ModelAdmin):
    list_display = ('semester', 'year', 'department', 'created_by', 'shared_with_students', 'shared_with_teachers', 'created_at')
    list_filter = ('shared_with_students', 'shared_with_teachers', 'department')
    search_fields = ('semester', 'year')
    ordering = ('-created_at',)


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ('date', 'title', 'type', 'color_code', 'calendar')
    list_filter = ('type', 'calendar')
    search_fields = ('title', 'description')
    ordering = ('date',)


@admin.register(EventTypeColor)
class EventTypeColorAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'color_code', 'updated_at')
    search_fields = ('event_type',)
