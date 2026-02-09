import os
import django
import datetime
import sys
from pathlib import Path

# Setup paths relative to script location
# Assuming script is in EduSync/scripts/seed.py
CURRENT_DIR = Path(__file__).resolve().parent
BASE_DIR = CURRENT_DIR.parent 
sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduSync.settings')
django.setup()

from django.contrib.auth.models import User
from generator.models import TimetableEntry, Division, TimeSlot, Room, Timetable
from academics.models import Course
from teacher.models import Teacher
from institution.models import Institution
from accounts.models import UserProfile

def run():
    print("--- EduSync Data Seeding Started ---")
    
    print("Checking for existing admin user...")
    if not User.objects.filter(username='admin').exists():
        admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        print("Created superuser 'admin' with password 'admin123'")
    else:
        admin_user = User.objects.get(username='admin')
        print("Using existing superuser 'admin'")

    # Create Institution
    institution_name = "EduSync University"
    institution, created = Institution.objects.get_or_create(
        name=institution_name,
        admin=admin_user,
        defaults={'email': 'info@edusync.com', 'address': 'Campus Drive, University City'}
    )
    if created:
        print(f"Created Institution: {institution.name}")
        # Ensure admin has a UserProfile
        UserProfile.objects.get_or_create(
            user=admin_user,
            defaults={'role': 'institution_admin', 'institution': institution_name}
        )
    else:
        print(f"Using existing Institution: {institution.name}")

    # Create a default Timetable
    active_tt, created = Timetable.objects.get_or_create(
        institution=institution,
        is_active=True,
        defaults={'name': 'Spring 2024 Semester', 'days_count': 6}
    )
    
    if not created:
        print(f"Using existing active timetable: {active_tt.name}")
    else:
        print(f"Created new timetable: {active_tt.name}")

    # Create Divisions
    if not active_tt.divisions.exists():
        divs = [Division.objects.create(name=f"D{i}", timetable=active_tt) for i in range(1, 4)]
        print(f"Created {len(divs)} divisions (D1, D2, D3)")
    else:
        divs = list(active_tt.divisions.all())

    # Create Teachers
    teachers_data = [
        ("Dr. Alan Turing", "AT"),
        ("Prof. Ada Lovelace", "AL"),
        ("Dr. Grace Hopper", "GH"),
    ]
    
    teachers = {}
    for name, initials in teachers_data:
        username = initials.lower()
        user, u_created = User.objects.get_or_create(
            username=username,
            defaults={'first_name': name.split()[1], 'last_name': name.split()[-1]}
        )
        if u_created:
            user.set_password('password123')
            user.save()
            
        teacher, _ = Teacher.objects.get_or_create(
            user=user,
            institution=institution,
            defaults={
                'employee_id': f"EMP_{initials}",
                'department': 'Computer Science',
                'qualification': 'PhD',
            }
        )
        teachers[initials] = teacher
    print(f"Ensured {len(teachers)} teachers exist.")

    # Create Courses
    courses_data = [
        ("Data Structures", "CS201"),
        ("Algorithms", "CS301"),
        ("Web Development", "CS105"),
        ("Database Systems", "CS401"),
    ]
    
    courses = {}
    for name, code in courses_data:
        course, _ = Course.objects.get_or_create(
            institution=institution,
            code=code,
            defaults={'name': name}
        )
        courses[code] = course
    print(f"Ensured {len(courses)} courses exist.")

    # Create Rooms
    rooms_data = ["Lab 101", "Lecture Hall 4", "Room 205"]
    rooms = {}
    for num in rooms_data:
        room, _ = Room.objects.get_or_create(
            institution=institution,
            number=num
        )
        rooms[num] = room
    print(f"Ensured {len(rooms)} rooms exist.")

    # TimeSlots if they don't exist
    if not active_tt.timeslots.exists():
        TimeSlot.objects.create(timetable=active_tt, lecture_number=1, start_time=datetime.time(9,0), end_time=datetime.time(10,0))
        TimeSlot.objects.create(timetable=active_tt, lecture_number=2, start_time=datetime.time(10,0), end_time=datetime.time(11,0))
        TimeSlot.objects.create(timetable=active_tt, lecture_number=3, start_time=datetime.time(11,0), end_time=datetime.time(11,30), is_break=True)
        TimeSlot.objects.create(timetable=active_tt, lecture_number=4, start_time=datetime.time(11,30), end_time=datetime.time(12,30))
        print("Created default time slots.")

    print("--- Seeding Complete! ---")
    print("You can now login with admin / admin123")

if __name__ == '__main__':
    run()
