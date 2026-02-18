"""Quick script to recreate timetable entries with better distribution"""
import os, sys, django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduSync.settings')
django.setup()

from generator.models import Timetable, TimetableEntry, Room
from teacher.models import Teacher
from academics.models import Course
from institution.models import Institution

inst = Institution.objects.get(name='Prestige Academy')
tt = Timetable.objects.get(id=58)

# Clear existing entries
TimetableEntry.objects.filter(timetable=tt).delete()
print("Deleted old entries")

# Get resources
teachers = list(Teacher.objects.filter(institution=inst, user__username__startswith='teacher').order_by('id'))
subjects = list(Course.objects.filter(institution=inst, code__startswith='CS3').order_by('id'))
if not subjects:
    subjects = list(Course.objects.filter(institution=inst).order_by('id'))[:8]
rooms = list(Room.objects.filter(institution=inst).order_by('id'))
divisions = list(tt.divisions.all())
time_slots = list(tt.timeslots.filter(is_break=False).order_by('lecture_number'))
days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']

print(f"Teachers: {len(teachers)}, Subjects: {len(subjects)}, Rooms: {len(rooms)}, Divisions: {len(divisions)}, Slots: {len(time_slots)}")

teacher_idx = 0
cnt = 0

for day in days:
    for slot in time_slots:
        for div_idx, division in enumerate(divisions):
            subject = subjects[(cnt) % len(subjects)]
            teacher = teachers[teacher_idx % len(teachers)]
            teacher_idx += 1  # Each entry gets a different teacher
            room = rooms[div_idx % len(rooms)]
            
            try:
                TimetableEntry.objects.create(
                    timetable=tt,
                    day=day,
                    timeslot=slot,
                    division=division,
                    subject=subject,
                    faculty=teacher,
                    room=room
                )
                cnt += 1
            except Exception as e:
                print(f"Skipped conflict: {day} {slot} {division} - {e}")

print(f"Created {cnt} entries")

# Show distribution
from collections import Counter
entries = TimetableEntry.objects.filter(timetable=tt)
teacher_counts = Counter(e.faculty.user.username for e in entries if e.faculty)
print(f"Teacher distribution: {dict(teacher_counts)}")
