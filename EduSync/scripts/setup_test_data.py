"""
Setup Test Data Script for Prestige Academy
Creates 20 students and 20 teachers with all details filled
Sets password '123' for all users
Creates proper timetable with teacher assignments
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduSync.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import transaction
from datetime import date, time
from institution.models import Institution, Department
from academics.models import Branch, Course
from teacher.models import Teacher
from student.models import Student
from generator.models import Timetable, Division, TimeSlot, TimetableEntry, Room
from accounts.models import UserProfile

# Configuration
PASSWORD = '123'
INSTITUTION_NAME = 'Prestige Academy'

# Sample names for students
STUDENT_NAMES = [
    ('Aarav', 'Sharma'), ('Vivaan', 'Patel'), ('Aditya', 'Singh'), ('Vihaan', 'Kumar'),
    ('Arjun', 'Gupta'), ('Sai', 'Reddy'), ('Reyansh', 'Joshi'), ('Ayaan', 'Shah'),
    ('Krishna', 'Verma'), ('Ishaan', 'Mehta'), ('Priya', 'Desai'), ('Ananya', 'Rao'),
    ('Diya', 'Iyer'), ('Aanya', 'Nair'), ('Aadhya', 'Pillai'), ('Myra', 'Menon'),
    ('Sara', 'Chopra'), ('Saanvi', 'Malhotra'), ('Anika', 'Kapoor'), ('Navya', 'Saxena')
]

# Sample names for teachers
TEACHER_NAMES = [
    ('Dr. Rajesh', 'Khanna'), ('Prof. Anjali', 'Sharma'), ('Dr. Vikram', 'Thakur'),
    ('Prof. Sunita', 'Devi'), ('Dr. Manoj', 'Kumar'), ('Prof. Kavita', 'Jain'),
    ('Dr. Suresh', 'Pandey'), ('Prof. Neha', 'Agarwal'), ('Dr. Amit', 'Verma'),
    ('Prof. Pooja', 'Yadav'), ('Dr. Ramesh', 'Mishra'), ('Prof. Swati', 'Chauhan'),
    ('Dr. Anil', 'Dubey'), ('Prof. Meena', 'Srivastava'), ('Dr. Sanjay', 'Trivedi'),
    ('Prof. Ritu', 'Bhargava'), ('Dr. Prakash', 'Tiwari'), ('Prof. Shweta', 'Rastogi'),
    ('Dr. Deepak', 'Awasthi'), ('Prof. Nidhi', 'Shukla')
]

# Subjects/Courses to create
SUBJECTS = [
    ('CS301', 'Data Structures & Algorithms'),
    ('CS302', 'Database Management Systems'),
    ('CS303', 'Operating Systems'),
    ('CS304', 'Computer Networks'),
    ('CS305', 'Web Development'),
    ('CS306', 'Software Engineering'),
    ('MA301', 'Engineering Mathematics'),
    ('PH301', 'Applied Physics'),
]

def run():
    with transaction.atomic():
        print("=" * 60)
        print("Setting up test data for Prestige Academy")
        print("=" * 60)
        
        # 1. Get Prestige Academy
        try:
            institution = Institution.objects.get(name=INSTITUTION_NAME)
            print(f"✓ Found institution: {institution.name} (ID: {institution.id})")
        except Institution.DoesNotExist:
            print(f"✗ Institution '{INSTITUTION_NAME}' not found!")
            return
        
        # 2. Get or create Department
        dept, created = Department.objects.get_or_create(
            institution=institution,
            name='SY1',
            defaults={'description': 'Second Year - Division 1'}
        )
        print(f"{'✓ Created' if created else '✓ Found'} department: {dept.name} (ID: {dept.id})")
        
        # 3. Get or create Branch for SY1
        branch, created = Branch.objects.get_or_create(
            institution=institution,
            department=dept,
            name='Computer Science',
            defaults={'description': 'Computer Science and Engineering'}
        )
        print(f"{'✓ Created' if created else '✓ Found'} branch: {branch.name} (ID: {branch.id})")
        
        # 4. Create/Get Rooms
        rooms = []
        for room_num in ['101', '102', '103', '104', '105']:
            room, _ = Room.objects.get_or_create(
                institution=institution,
                number=room_num
            )
            rooms.append(room)
        print(f"✓ Created/found {len(rooms)} rooms")
        
        # 5. Create/Get Subjects (Courses)
        subjects = []
        for code, name in SUBJECTS:
            course, created = Course.objects.get_or_create(
                institution=institution,
                code=code,
                defaults={
                    'name': name,
                    'description': f'{name} course',
                    'credits': 3,
                    'department': dept
                }
            )
            subjects.append(course)
        print(f"✓ Created/found {len(subjects)} subjects/courses")
        
        # 6. Create 20 Teachers
        print("\n--- Creating 20 Teachers ---")
        teachers = []
        for i, (first, last) in enumerate(TEACHER_NAMES):
            username = f"teacher{i+1:02d}"
            email = f"{username}@prestige.edu"
            emp_id = f"TCH{2024}{i+1:03d}"
            
            # Get or create user
            user, user_created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first.replace('Dr. ', '').replace('Prof. ', ''),
                    'last_name': last,
                    'email': email,
                    'is_active': True
                }
            )
            if user_created or True:  # Always set password
                user.set_password(PASSWORD)
                user.first_name = first.replace('Dr. ', '').replace('Prof. ', '')
                user.last_name = last
                user.save()
            
            # Create UserProfile
            profile, _ = UserProfile.objects.get_or_create(
                user=user,
                defaults={'role': 'teacher'}
            )
            profile.role = 'teacher'
            profile.save()
            
            # Create Teacher record
            teacher, created = Teacher.objects.get_or_create(
                user=user,
                defaults={
                    'institution': institution,
                    'employee_id': emp_id,
                    'department': dept,
                    'branch': branch,
                    'qualification': 'M.Tech, Ph.D' if 'Dr.' in first else 'M.Tech',
                    'gender': 'F' if first in ['Prof. Anjali', 'Prof. Sunita', 'Prof. Kavita', 'Prof. Neha', 'Prof. Pooja', 'Prof. Swati', 'Prof. Meena', 'Prof. Ritu', 'Prof. Shweta', 'Prof. Nidhi'] else 'M',
                    'date_of_birth': date(1975 + (i % 15), (i % 12) + 1, (i % 28) + 1),
                    'phone': f'98765{i:05d}',
                    'address': f'{100 + i} Faculty Housing, Prestige Campus',
                    'salary': 50000 + (i * 5000),
                    'contract_type': 'Full-Time'
                }
            )
            if not created:
                teacher.institution = institution
                teacher.department = dept
                teacher.branch = branch
                teacher.save()
            
            teachers.append(teacher)
            
            # Assign teacher to subjects
            if i < len(subjects):
                subjects[i % len(subjects)].teachers.add(teacher)
            
            status = "Created" if created else "Updated"
            print(f"  [{i+1:02d}] {status}: {username} / {PASSWORD} - {first} {last}")
        
        # 7. Create 20 Students
        print("\n--- Creating 20 Students ---")
        students = []
        for i, (first, last) in enumerate(STUDENT_NAMES):
            username = f"student{i+1:02d}"
            email = f"{username}@prestige.edu"
            stu_id = f"PA{2024}{i+1:03d}"
            
            # Get or create user
            user, user_created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first,
                    'last_name': last,
                    'email': email,
                    'is_active': True
                }
            )
            if user_created or True:  # Always set password
                user.set_password(PASSWORD)
                user.first_name = first
                user.last_name = last
                user.save()
            
            # Create UserProfile
            profile, _ = UserProfile.objects.get_or_create(
                user=user,
                defaults={'role': 'student'}
            )
            profile.role = 'student'
            profile.save()
            
            # Check if student exists for this user
            try:
                student = Student.objects.get(user=user)
                # Update existing student
                student.institution = institution
                student.student_id = stu_id if not Student.objects.filter(student_id=stu_id).exclude(user=user).exists() else student.student_id
                student.department = dept
                student.branch = branch
                student.course = subjects[0] if subjects else None
                student.save()
                created = False
            except Student.DoesNotExist:
                # Check if student_id is taken
                while Student.objects.filter(student_id=stu_id).exists():
                    stu_id = f"PA{2024}{i+100:03d}"
                    i += 100
                
                student = Student.objects.create(
                    user=user,
                    institution=institution,
                    student_id=stu_id,
                    department=dept,
                    branch=branch,
                    course=subjects[0] if subjects else None,
                    phone=f'91234{i:05d}',
                    academic_year='2024-2025',
                    gender='F' if i >= 10 else 'M',
                    date_of_birth=date(2002 + (i % 3), (i % 12) + 1, (i % 28) + 1),
                    address=f'{200 + i} Student Hostel, Prestige Campus',
                    parent_name=f'Mr./Mrs. {last}',
                    parent_phone=f'98888{i:05d}',
                    blood_group=['A+', 'B+', 'O+', 'AB+', 'A-', 'B-'][i % 6],
                    semester=3,
                    status='active'
                )
                created = True
            
            students.append(student)
            status = "Created" if created else "Updated"
            print(f"  [{i+1:02d}] {status}: {username} / {PASSWORD} - {first} {last}")
        
        # 8. Create Timetable
        print("\n--- Creating Timetable ---")
        
        # Delete old timetables for this dept/branch to avoid conflicts
        old_tts = Timetable.objects.filter(department=dept, branch=branch)
        if old_tts.exists():
            print(f"  Removing {old_tts.count()} old timetable(s)...")
            old_tts.delete()
        
        timetable = Timetable.objects.create(
            institution=institution,
            department=dept,
            branch=branch,
            name=f'{dept.name} {branch.name} Timetable',
            status='Published',
            is_active=True,
            is_published=True,
            days_count=6,
            heading_1='PRESTIGE ACADEMY',
            heading_2=f'{dept.name} - {branch.name}',
            footer_semester_text='SEMESTER III',
            footer_prepared_by='Prepared By: Academic Committee',
            footer_hod='Prof. Rajesh Khanna\nHOD - Computer Science',
        )
        print(f"✓ Created timetable: {timetable.name} (ID: {timetable.id})")
        
        # 9. Create Divisions
        divisions = []
        for div_name in ['D1', 'D2']:
            div = Division.objects.create(timetable=timetable, name=div_name)
            divisions.append(div)
        print(f"✓ Created {len(divisions)} divisions: {[d.name for d in divisions]}")
        
        # 10. Assign students to divisions
        for i, student in enumerate(students):
            student.division = divisions[i % len(divisions)]
            student.save()
        print("✓ Assigned students to divisions")
        
        # 11. Create TimeSlots
        time_slots_data = [
            (1, time(9, 0), time(10, 0), False),
            (2, time(10, 0), time(11, 0), False),
            (3, time(11, 0), time(11, 15), True),  # Break
            (4, time(11, 15), time(12, 15), False),
            (5, time(12, 15), time(13, 15), False),
            (6, time(13, 15), time(14, 0), True),  # Lunch
            (7, time(14, 0), time(15, 0), False),
            (8, time(15, 0), time(16, 0), False),
        ]
        
        timeslots = []
        for lec_num, start, end, is_break in time_slots_data:
            ts = TimeSlot.objects.create(
                timetable=timetable,
                lecture_number=lec_num,
                start_time=start,
                end_time=end,
                is_break=is_break
            )
            timeslots.append(ts)
        print(f"✓ Created {len(timeslots)} time slots")
        
        # 12. Create Timetable Entries
        days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']
        entries_created = 0
        
        lecture_slots = [ts for ts in timeslots if not ts.is_break]
       
        # Track used faculty per slot per day to avoid conflicts
        teacher_index = 0
        
        for day_idx, day in enumerate(days):
            for slot_idx, slot in enumerate(lecture_slots):
                # For each division, assign different teachers
                for div_idx, division in enumerate(divisions):
                    # Rotate subjects
                    subject_idx = (day_idx * len(lecture_slots) + slot_idx + div_idx) % len(subjects)
                    
                    # Assign different teachers for each division in the same slot
                    # Increment teacher_index to ensure no conflicts
                    teacher = teachers[teacher_index % len(teachers)]
                    teacher_index += 1
                    
                    room_idx = div_idx % len(rooms)
                    
                    try:
                        TimetableEntry.objects.create(
                            timetable=timetable,
                            day=day,
                            timeslot=slot,
                            division=division,
                            subject=subjects[subject_idx],
                            faculty=teacher,
                            room=rooms[room_idx]
                        )
                        entries_created += 1
                    except Exception as e:
                        # Skip conflicts (same room/faculty at same time)
                        pass
        
        print(f"✓ Created {entries_created} timetable entries")
        
        # Summary
        print("\n" + "=" * 60)
        print("SETUP COMPLETE!")
        print("=" * 60)
        print(f"\nInstitution: {institution.name}")
        print(f"Department: {dept.name}")
        print(f"Branch: {branch.name}")
        print(f"Timetable: {timetable.name} (Active: {timetable.is_active}, Published: {timetable.is_published})")
        print(f"\nTeachers: {len(teachers)} (Login: teacher01 to teacher20, Password: {PASSWORD})")
        print(f"Students: {len(students)} (Login: student01 to student20, Password: {PASSWORD})")
        print(f"\nStudents can view timetable at: /student/timetable/")
        print(f"Teachers can view schedule on their dashboard: /teacher/dashboard/")
        
        return True

if __name__ == '__main__':
    success = run()
    if success:
        print("\n✓ All done!")
    else:
        print("\n✗ Script failed!")
