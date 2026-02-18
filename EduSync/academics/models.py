from django.db import models
from django.conf import settings
from teacher.models import Teacher
from institution.models import Institution


class Branch(models.Model):
    institution = models.ForeignKey(
        Institution, on_delete=models.CASCADE
    )
    department = models.ForeignKey(
        'institution.Department', on_delete=models.SET_NULL, null=True, blank=True
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Course(models.Model):
    institution = models.ForeignKey(
        Institution, on_delete=models.CASCADE, db_index=True
    )
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    teachers = models.ManyToManyField(
        Teacher, blank=True
    )
    credits = models.IntegerField(default=3)
    duration_months = models.PositiveIntegerField(default=0)
    department = models.ForeignKey('institution.Department', on_delete=models.SET_NULL, null=True, blank=True)
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('institution', 'code')

    def __str__(self):
        return f"{self.code} - {self.name}"


class Grade(models.Model):
    GRADE_CHOICES = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
        ('F', 'F'),
    ]

    student = models.ForeignKey(
        'student.Student', on_delete=models.CASCADE
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE
    )
    grade = models.CharField(
        max_length=1, choices=GRADE_CHOICES
    )
    marks = models.FloatField()
    date_assigned = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student} - {self.course} : {self.grade}"


class AttendanceSheet(models.Model):
    """Generated attendance sheet for a department during a period"""
    teacher = models.ForeignKey('teacher.Teacher', on_delete=models.CASCADE)
    department = models.ForeignKey('institution.Department', on_delete=models.CASCADE)
    date_from = models.DateField()
    date_to = models.DateField()
    total_lectures = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    shared_with_students = models.BooleanField(default=False)

    class Meta:
        unique_together = ('teacher', 'department', 'date_from', 'date_to')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.teacher} - {self.department.name} ({self.date_from} to {self.date_to})"


class Attendance(models.Model):
    """Individual attendance record for a student"""
    sheet = models.ForeignKey(AttendanceSheet, on_delete=models.CASCADE, related_name='attendance_records')
    student = models.ForeignKey('student.Student', on_delete=models.CASCADE, related_name='attendance_records')
    lectures_attended = models.PositiveIntegerField(default=0)
    total_lectures = models.PositiveIntegerField()

    class Meta:
        unique_together = ('sheet', 'student')
        ordering = ['student__student_id']

    def __str__(self):
        return f"{self.student} - {self.lectures_attended}/{self.total_lectures}"

    @property
    def attendance_percentage(self):
        """Calculate attendance percentage"""
        if self.total_lectures == 0:
            return 0
        return round((self.lectures_attended / self.total_lectures) * 100, 2)


class AcademicCalendar(models.Model):
    """Editable academic calendar per semester and academic year.

    New fields `shared_with_students` and `shared_with_teachers` allow admins to
    make specific calendars visible to students/teachers without granting edit
    access.
    """

    semester = models.CharField(max_length=30)
    year = models.CharField(max_length=20)

    # optional: target this calendar to a specific Department (null = all departments)
    department = models.ForeignKey(
        'institution.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='calendars'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='academic_calendars'
    )

    # admin-controlled visibility flags
    shared_with_students = models.BooleanField(default=False)
    shared_with_teachers = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'academic_calendar'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.semester} ({self.year})"


class CalendarEvent(models.Model):
    """Day-wise academic calendar events."""

    EVENT_TYPES = [
        ('Regular Teaching', 'Regular Teaching'),
        ('Test', 'Test'),
        ('Reading Holiday', 'Reading Holiday'),
        ('Public Holiday', 'Public Holiday'),
        ('Semester Break', 'Semester Break'),
        ('Festival Holiday', 'Festival Holiday'),
        ('Project / Practical Evaluation', 'Project / Practical Evaluation'),
    ]

    # Default color palette mapped to event types (used by UI and form defaults)
    DEFAULT_TYPE_COLORS = {
        'Regular Teaching': '#3B82F6',
        'Test': '#EF4444',
        'Reading Holiday': '#F59E0B',
        'Public Holiday': '#10B981',
        'Semester Break': '#64748B',
        'Festival Holiday': '#F97316',
        'Project / Practical Evaluation': '#6366F1',
    }

    calendar = models.ForeignKey(
        AcademicCalendar,
        on_delete=models.CASCADE,
        related_name='events'
    )
    date = models.DateField()
    title = models.CharField(max_length=150)
    type = models.CharField(max_length=50, choices=EVENT_TYPES)
    description = models.TextField(blank=True)
    color_code = models.CharField(max_length=20, default='#2563EB')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'calendar_events'
        ordering = ['date', 'id']

    def __str__(self):
        return f"{self.date} - {self.title}"

    @classmethod
    def get_type_color_mapping(cls):
        """Return a mapping of event_type -> color.
        Prefers values configured in EventTypeColor (DB); falls back to DEFAULT_TYPE_COLORS.
        Safe to call during migrations/tests (silently falls back on DB errors).
        """
        mapping = dict(cls.DEFAULT_TYPE_COLORS)
        try:
            # EventTypeColor may not exist yet during migrations — guard with try/except
            for override in EventTypeColor.objects.all():
                mapping[override.event_type] = override.color_code
        except Exception:
            # any DB access error -> return static defaults
            pass
        return mapping

    @classmethod
    def color_for_type(cls, ev_type):
        """Single-value lookup with fallback."""
        return cls.get_type_color_mapping().get(ev_type, cls.DEFAULT_TYPE_COLORS.get(ev_type, '#2563EB'))


class EventTypeColor(models.Model):
    """Database-backed overrides for per-event-type colors.

    Admins can edit these to change the color presented for each event type.
    CalendarEvent.get_type_color_mapping() prefers these values when present.
    """
    EVENT_TYPE_CHOICES = CalendarEvent.EVENT_TYPES

    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES, unique=True)
    color_code = models.CharField(max_length=20, default='#2563EB')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'event_type_colors'
        ordering = ['event_type']

    def __str__(self):
        return f"{self.event_type} ({self.color_code})"
