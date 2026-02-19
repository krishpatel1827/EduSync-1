from django.contrib import admin
from .models import Institution, News, Department, AcademicCalendarEvent

@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone')
    search_fields = ('name', 'email')

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'institution', 'created_at')
    list_filter = ('institution',)
    search_fields = ('content',)
    ordering = ('-created_at',)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'institution', 'created_at')
    list_filter = ('institution',)
    search_fields = ('name',)

@admin.register(AcademicCalendarEvent)
class AcademicCalendarEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'institution', 'event_type', 'start_date', 'end_date', 'is_published')
    list_filter = ('event_type', 'is_published', 'institution')
    search_fields = ('title', 'description')
    ordering = ('start_date',)

