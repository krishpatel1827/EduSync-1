from django.contrib import admin
from .models import Course, Grade, AttendanceSheet, Attendance, Branch


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
