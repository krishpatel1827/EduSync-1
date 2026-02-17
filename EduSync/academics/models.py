from django.db import models
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
