from django.contrib import admin
from institution.models import Department
from academics.models import Course as Subject # Use existing Course
from .models import TeacherSubject, Marksheet, Marks

# Note: Using existing Student model from student app, not registering separate StudentProfile

@admin.register(TeacherSubject)
class TeacherSubjectAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'subject', 'subject__department')
    list_filter = ('subject__department',)

class MarksInline(admin.TabularInline):
    model = Marks
    extra = 0

@admin.register(Marksheet)
class MarksheetAdmin(admin.ModelAdmin):
    list_display = ('student', 'semester', 'academic_year', 'total_marks', 'percentage', 'final_grade')
    list_filter = ('semester', 'academic_year', 'final_grade')
    search_fields = ('student__username',)
    inlines = [MarksInline]
    readonly_fields = ('total_marks', 'percentage', 'final_grade')

@admin.register(Marks)
class MarksAdmin(admin.ModelAdmin):
    list_display = ('marksheet', 'subject', 'marks', 'grade')
    list_filter = ('subject', 'grade')
