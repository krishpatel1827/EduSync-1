import os
import django
import random
from datetime import date, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduSync.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import UserProfile
from institution.models import Institution, Department, News
from academics.models import Course, Branch, AttendanceSheet, Attendance
from teacher.models import Teacher
from student.models import Student
from generator.models import Timetable, TimetableEntry, TimeSlot, Room, Division

def generate_dummy_data():
    print("🚀 Starting comprehensive dummy data generation...")

    # 1. Create Institution Admin
    admin_username = 'test_admin_new'
    if not User.objects.filter(username=admin_username).exists():
        admin_user = User.objects.create_superuser(admin_username, 'admin@test.com', 'admin123')
        print(f"✅ Created Admin User: {admin_username}")
    else:
        admin_user = User.objects.get(username=admin_username)
        print(f"ℹ️ Admin User {admin_username} already exists")

    # Sync UserProfile
    profile, created = UserProfile.objects.get_or_create(user=admin_user)
    profile.role = 'institution_admin'
    profile.save()
    print(f"✅ Admin Profile synced (Role: {profile.role})")

    # 2. Create Institution
    inst_name = 'Test University 2026'
    institution, created = Institution.objects.get_or_create(
        admin=admin_user,
        defaults={'name': inst_name, 'address': '123 test street', 'email': 'contact2026@testuni.edu'}
    )
    if created:
        print(f"✅ Created Institution: {inst_name}")
    else:
        print(f"ℹ️ Institution {inst_name} already exists")

    # 3. Create Departments
    depts = ['Computer Science', 'Electronic Engineering', 'Business Management']
    dept_objects = []
    for d_name in depts:
        dept, created = Department.objects.get_or_create(institution=institution, name=d_name)
        dept_objects.append(dept)
        if created: print(f"✅ Created Department: {d_name}")

    # 4. Create Branches
    branches_map = {
        'Computer Science': ['AI & ML', 'Cyber Security', 'Software Engineering'],
        'Electronic Engineering': ['Robotics', 'VLSI Design'],
        'Business Management': ['Finance', 'Marketing']
    }
    branch_objects = []
    for dept in dept_objects:
        for b_name in branches_map.get(dept.name, []):
            branch, created = Branch.objects.get_or_create(institution=institution, department=dept, name=b_name)
            branch_objects.append(branch)
            if created: print(f"✅ Created Branch: {b_name} in {dept.name}")

    # 5. Create Teachers
    teachers = []
    for i in range(1, 4):
        t_username = f'teacher_new_{i}'
        if not User.objects.filter(username=t_username).exists():
            u = User.objects.create_user(t_username, f'{t_username}@test.com', 'teacher123')
            print(f"✅ Created User for Teacher: {t_username}")
        else:
            u = User.objects.get(username=t_username)

        profile, _ = UserProfile.objects.get_or_create(user=u)
        profile.role = 'teacher'
        profile.save()
        
        t, created = Teacher.objects.get_or_create(
            user=u,
            defaults={
                'institution': institution,
                'department': random.choice(dept_objects),
                'employee_id': f'EMP{200+i}',
                'phone': '1234567890'
            }
        )
        teachers.append(t)
        if created: print(f"✅ Created Teacher Profile: {t_username} (ID: {t.employee_id})")

    # 6. Create Courses
    course_objects = []
    courses_data = [
        ('CS101', 'Intro to Programming', 'Computer Science'),
        ('CS102', 'Data Structures', 'Computer Science'),
        ('EE201', 'Digital Electronics', 'Electronic Engineering'),
        ('BM301', 'Principles of Finance', 'Business Management'),
    ]
    for code, name, d_name in courses_data:
        dept = next(d for d in dept_objects if d.name == d_name)
        course, created = Course.objects.get_or_create(
            institution=institution, 
            code=code, 
            defaults={'name': name, 'department': dept, 'credits': 4}
        )
        if created:
            teacher = random.choice([t for t in teachers if t.department == dept] or teachers)
            course.teachers.add(teacher)
            print(f"✅ Created Course: {name} ({code}) with Teacher {teacher.user.username}")
        course_objects.append(course)

    # 7. Create Students
    student_objects = []
    for i in range(1, 6):
        s_username = f'student_new_{i}'
        if not User.objects.filter(username=s_username).exists():
            u = User.objects.create_user(s_username, f'{s_username}@test.com', 'student123')
            print(f"✅ Created User for Student: {s_username}")
        else:
            u = User.objects.get(username=s_username)

        profile, _ = UserProfile.objects.get_or_create(user=u)
        profile.role = 'student'
        profile.save()
        
        branch = random.choice(branch_objects)
        s, created = Student.objects.get_or_create(
            user=u,
            defaults={
                'institution': institution,
                'department': branch.department,
                'branch': branch,
                'student_id': f'STU{200+i}',
                'phone': '0987654321',
                'academic_year': '2024'
            }
        )
        student_objects.append(s)
        if created: print(f"✅ Created Student Profile: {s_username} (ID: {s.student_id})")

    # 8. Create news
    News.objects.create(institution=institution, content="Welcome to the updated EduSync Portal! Check out the new attendance features.")
    News.objects.create(institution=institution, content="Institution-wide hackathon announced for next month.")

    # 9. Create Attendance Data
    for dept in dept_objects:
        teacher = Teacher.objects.filter(department=dept).first()
        if teacher:
            sheet, _ = AttendanceSheet.objects.get_or_create(
                teacher=teacher,
                department=dept,
                date_from=date.today() - timedelta(days=30),
                date_to=date.today(),
                defaults={'total_lectures': 20, 'shared_with_students': True}
            )
            dept_students = Student.objects.filter(department=dept)
            for s in dept_students:
                Attendance.objects.get_or_create(
                    sheet=sheet,
                    student=s,
                    defaults={'total_lectures': 20, 'lectures_attended': random.randint(12, 20)}
                )
            print(f"✅ Created/Verified Attendance Sheet for {dept.name} (Shared)")

    # 10. Create Timetable Data
    # Rooms
    room1, _ = Room.objects.get_or_create(institution=institution, number="101")
    room2, _ = Room.objects.get_or_create(institution=institution, number="102")

    for dept in dept_objects:
        course = Course.objects.filter(department=dept).first()
        if course:
            tt, created = Timetable.objects.get_or_create(
                institution=institution,
                department=dept,
                course=course,
                defaults={'name': f"Timetable - {course.code}", 'is_active': True}
            )
            
            # Divisions
            divA, _ = Division.objects.get_or_create(timetable=tt, name="Div A")
            
            # TimeSlots (must be linked to timetable)
            ts1, _ = TimeSlot.objects.get_or_create(timetable=tt, lecture_number=1, defaults={'start_time': "09:00:00", 'end_time': "10:00:00"})
            ts2, _ = TimeSlot.objects.get_or_create(timetable=tt, lecture_number=2, defaults={'start_time': "10:00:00", 'end_time': "11:00:00"})

            # Add some entries
            for day in ['MON', 'TUE', 'WED', 'THU', 'FRI']:
                faculty = course.teachers.first() or random.choice(teachers)
                TimetableEntry.objects.get_or_create(
                    timetable=tt,
                    day=day,
                    timeslot=ts1 if day in ['MON', 'WED', 'FRI'] else ts2,
                    division=divA,
                    defaults={'subject': course, 'faculty': faculty, 'room': room1}
                )
            print(f"✅ Created/Verified Timetable for {course.name}")

    print("\n" + "="*50)
    print("🎉 DUMMY DATA GENERATION COMPLETE!")
    print(f"Admin Username:   {admin_username}")
    print(f"Teacher Username: teacher_new_1")
    print(f"Student Username: student_new_1")
    print("Password (All):   admin123 / teacher123 / student123")
    print("="*50)

if __name__ == '__main__':
    generate_dummy_data()
