from django.db import models
from django.contrib.auth.models import User

class Institution(models.Model):
    name = models.CharField(max_length=200, unique=True)
    admin = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True)
    established_year = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Department(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('institution', 'name')

class News(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='news_feed', null=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.content[:30]


class AcademicCalendarEvent(models.Model):
    """Academic calendar events like exams, holidays, semester dates, etc."""
    EVENT_TYPES = [
        ('exam', 'Examination'),
        ('holiday', 'Holiday'),
        ('semester_start', 'Semester Start'),
        ('semester_end', 'Semester End'),
        ('event', 'Event'),
        ('deadline', 'Deadline'),
        ('other', 'Other'),
    ]
    
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='calendar_events')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='event')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['start_date', 'title']
    
    def __str__(self):
        return f"{self.title} ({self.start_date})"
