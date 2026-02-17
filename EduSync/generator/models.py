from django.db import models
from academics.models import Course
from teacher.models import Teacher
from institution.models import Institution

class Timetable(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, null=True, blank=True)
    department = models.ForeignKey('institution.Department', on_delete=models.CASCADE, null=True, blank=True)
    course = models.ForeignKey('academics.Course', on_delete=models.CASCADE, null=True, blank=True)
    branch = models.ForeignKey('academics.Branch', on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    name = models.CharField(max_length=100, default="My Timetable")
    status = models.CharField(max_length=20, default='Draft', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)
    days_count = models.IntegerField(default=6)
    heading_1 = models.CharField(max_length=255, default="L.J. INSTITUTE OF ENGINEERING AND TECHNOLOGY, L.J. UNIVERSITY")
    heading_2 = models.CharField(max_length=255, default="SY CE/IT- 4 DEPARTMENT")
    
    # Footer Fields
    footer_semester_text = models.CharField(max_length=100, default="SEMESTER III")
    footer_prepared_by = models.TextField(default="Prepared By:\nProf. Darshan Bhatt (DVB)\nProf. Priyanka Sinha (PCS)")
    footer_hod = models.TextField(default="Prof. Sneha Shah\nHOD- SY4 (CST/CSIT/CSE_CS/MA&CP)")
    theme_palette = models.CharField(max_length=20, default="classic")

    def __str__(self):
        return f"{self.name} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

class Room(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, null=True, blank=True)
    number = models.CharField(max_length=20, help_text="e.g., 410-C")

    def __str__(self):
        return self.number

class Division(models.Model):
    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name='divisions', null=True, blank=True)
    name = models.CharField(max_length=10, help_text="e.g., D1")

    def __str__(self):
        return self.name

class TimeSlot(models.Model):
    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name='timeslots', null=True, blank=True)
    DAY_CHOICES = [
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
        ('SAT', 'Saturday'),
    ]
    lecture_number = models.IntegerField(help_text="1, 2, 3...")
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_break = models.BooleanField(default=False)

    class Meta:
        ordering = ['lecture_number']

    def __str__(self):
        return f"Rec {self.lecture_number}: {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"

class TimetableEntry(models.Model):
    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name='entries')
    day = models.CharField(max_length=3, choices=TimeSlot.DAY_CHOICES)
    
    # Relationships with CASCADE/PROTECT/SET_NULL as appropriate
    timeslot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    division = models.ForeignKey(Division, on_delete=models.CASCADE)
    subject = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True)
    faculty = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Timetable Entries"
        indexes = [
            models.Index(fields=['division']),
            models.Index(fields=['timeslot']),
        ]
        unique_together = [
            ('room', 'timeslot', 'day'),
            ('division', 'timeslot', 'day'),
            ('faculty', 'timeslot', 'day'),   
        ]
    
    def __str__(self):
        return f"{self.day} - {self.timeslot} - {self.division}"
