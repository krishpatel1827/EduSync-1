import os
import django
import random
from datetime import time

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduSync.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import UserProfile, SignupTable, LoginTable
from institution.models import Institution, Department
from academics.models import Branch, Course
from teacher.models import Teacher
from student.models import Student
from generator.models import Timetable, Room, Division, TimeSlot, TimetableEntry
from academics.models import AcademicCalendar, CalendarEvent
from marksheet.models import TeacherSubject, Marksheet, Marks
from datetime import date, timedelta

def create_ljiet_data():
    print("🚀 Starting dummy data generation for LJIET...")

    # 1. Create signup and login table entries first (required by unified login)
    inst_name = "LJIET"
    admin_pass = "Lj@123123"
    
    signup, created = SignupTable.objects.get_or_create(
        institution_name=inst_name,
        defaults={'email': 'admin@ljiet.edu.in'}
    )
    if created:
        print(f"✅ SignupTable entry created for {inst_name}")
        
    LoginTable.objects.get_or_create(
        signup=signup,
        institution_name=inst_name,
        defaults={'password': admin_pass}
    )

    # 2. Create Admin User for LJIET
    admin_username = "LJIET"
    
    admin_user, created = User.objects.get_or_create(username=admin_username)
    if created:
        admin_user.set_password(admin_pass)
        admin_user.save()
        print(f"✅ Admin user created: {admin_username}")
    
    admin_profile, _ = UserProfile.objects.get_or_create(user=admin_user)
    admin_profile.role = 'institution_admin'
    admin_profile.institution = inst_name # IMPORTANT
    admin_profile.save()

    # 3. Create Institution
    institution, created = Institution.objects.get_or_create(
        name=inst_name,
        defaults={'admin': admin_user, 'email': 'admin@ljiet.edu.in'}
    )
    if not created:
        institution.admin = admin_user
        institution.save()
    print(f"✅ Institution created/updated: {inst_name}")

    # 4. Create 4 Departments
    dept_names = ["SY1", "SY2", "SY3", "SY4"]
    departments = []
    for d_name in dept_names:
        dept, _ = Department.objects.get_or_create(
            name=d_name, 
            institution=institution,
            defaults={'description': f'Department {d_name} description'}
        )
        departments.append(dept)
    print(f"✅ {len(departments)} Departments created")

    # 5. Create 10 different branches
    branch_names = [
        "Computer Engineering", "Information Technology", "Artificial Intelligence", 
        "Data Science", "Cyber Security", "Electronics", "Mechanical Engineering",
        "Civil Engineering", "Cloud Computing", "Machine Learning"
    ]
    branches = []
    for b_name in branch_names:
        branch, _ = Branch.objects.get_or_create(
            name=b_name,
            institution=institution,
            defaults={'department': random.choice(departments)}
        )
        branches.append(branch)
    print(f"✅ {len(branches)} Branches created")

    # 6. Create 30 random Classrooms (Rooms)
    rooms = []
    for i in range(1, 31):
        room_num = f"L-{100 + i}"
        room, _ = Room.objects.get_or_create(
            number=room_num,
            institution=institution
        )
        rooms.append(room)
    print(f"✅ {len(rooms)} Rooms created")

    # 7. Pre-create Subjects (Courses) before students to assign them
    subj_list = [
        ("CS101", "Introduction to Computing"),
        ("MA102", "Engineering Mathematics"),
        ("DS103", "Data Structures"),
        ("AL104", "Algorithms"),
        ("DB105", "Database Management"),
        ("OS106", "Operating Systems"),
        ("NW107", "Computer Networks"),
        ("PY108", "Python Programming")
    ]
    subjects = []
    for code, name in subj_list:
        subj, _ = Course.objects.get_or_create(
            code=code,
            institution=institution,
            defaults={
                'name': name,
                'department': random.choice(departments),
                'credits': 4
            }
        )
        subjects.append(subj)
    print(f"✅ {len(subjects)} Subjects created")

    # 8. Pre-create Divisions for assignment
    divisions = []
    for i in range(1, 6):
        # We'll link these to a dummy timetable later if needed, but for now we need Division objects
        # Actually Timetable is required for Division in generator.models
        pass # Will handle inside the timetable loop below

    # Initialize Faker
    from faker import Faker
    fake = Faker()

    # 9. Create 35 Teachers (EMP80001 to EMP80035)
    teacher_pass = "Kv@321321"
    teachers = []
    quals = ["Ph.D. in Computer Science", "M.Tech in IT", "M.E. in Electronics", "Ph.D. in Mathematics", "M.Sc. in Physics"]
    contracts = ['Full-Time', 'Part-Time', 'Contract', 'Guest']
    
    teacher_names = [
        ("Simran", "Dhanvani"), ("Amit", "Sharma"), ("Neha", "Gupta"), ("Rajesh", "Kumar"), ("Priya", "Singh"),
        ("Vikram", "Mehta"), ("Anjali", "Desai"), ("Sanjay", "Patel"), ("Kavita", "Shah"), ("Deepak", "Verma"),
        ("Ritu", "Malhotra"), ("Sunil", "Joshi"), ("Megha", "Iyer"), ("Anand", "Reddy"), ("Shweta", "Bansal"),
        ("Manoj", "Tiwari"), ("Pooja", "Roy"), ("Ajay", "Mishra"), ("Swati", "Chawla"), ("Rahul", "Saxena"),
        ("Divya", "Pandey"), ("Sandeep", "Bakshi"), ("Rashmi", "Kulkarni"), ("Nitin", "Rao"), ("Sneha", "Bhatia"),
        ("Pankaj", "Kapoor"), ("Jyoti", "Agarwal"), ("Vishal", "Singh"), ("Monica", "Grewal"), ("Suresh", "Menon"),
        ("Archana", "Prabhu"), ("Gaurav", "Taneja"), ("Shalini", "Hegde"), ("Pratik", "Shinde"), ("Nishi", "Bhardwaj")
    ]
    
    for i in range(80001, 80036):
        t_username = f"EMP{i}"
        idx = i - 80001
        first_name, last_name = teacher_names[idx]
        
        user, created = User.objects.get_or_create(username=t_username)
        user.set_password(teacher_pass)
        user.first_name = first_name
        user.last_name = last_name
        user.email = f"{t_username.lower()}@ljiet.edu.in"
        user.save()
            
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = 'teacher'
        profile.institution = inst_name
        profile.phone = fake.phone_number()[:15]
        profile.save()
        
        teacher, created = Teacher.objects.get_or_create(
            user=user,
            institution=institution,
            defaults={
                'employee_id': f"ID-{i}",
                'department': random.choice(departments),
                'branch': random.choice(branches),
                'qualification': random.choice(quals),
                'gender': random.choice(['M', 'F']),
                'date_of_birth': fake.date_of_birth(minimum_age=25, maximum_age=60),
                'phone': fake.phone_number()[:15],
                'address': fake.address(),
                'salary': random.randint(50000, 150000),
                'contract_type': random.choice(contracts)
            }
        )
        # If already exists, update details to ensure they are filled
        if not created:
            teacher.qualification = random.choice(quals)
            teacher.gender = random.choice(['M', 'F'])
            teacher.date_of_birth = fake.date_of_birth(minimum_age=25, maximum_age=60)
            teacher.phone = fake.phone_number()[:15]
            teacher.address = fake.address()
            teacher.salary = random.randint(50000, 150000)
            teacher.contract_type = random.choice(contracts)
            teacher.save()

        teachers.append(teacher)
    print(f"✅ {len(teachers)} Teachers created with full details")

    # Now link teachers to subjects - Ensure EVERY teacher has at least 1 subject
    assigned_count = 0
    # First, make sure every teacher has one
    for t in teachers:
        subj = random.choice(subjects)
        TeacherSubject.objects.get_or_create(teacher=t.user, subject=subj)
        subj.teachers.add(t)
        assigned_count += 1
    
    # Then add some extra random assignments
    for subj in subjects:
        extras = random.sample(teachers, 2)
        for t in extras:
            TeacherSubject.objects.get_or_create(teacher=t.user, subject=subj)
            subj.teachers.add(t)
            assigned_count += 1
    print(f"✅ {assigned_count} total Teacher-Subject assignments created")

    # 10. Create 5 New Timetables and Divisions
    timetables = []
    all_divisions = []
    for i in range(1, 6):
        dept = departments[i % len(departments)]
        tt, _ = Timetable.objects.get_or_create(
            name=f"LJIET Master Schedule {i}",
            institution=institution,
            department=dept,
            defaults={
                'created_by': admin_user,
                'heading_1': "L.J. INSTITUTE OF ENGINEERING AND TECHNOLOGY",
                'heading_2': f"Department of {dept.name}",
                'status': 'Published',
                'is_published': True
            }
        )
        
        # Add basic TimeSlots if not exists
        if tt.timeslots.count() == 0:
            for j in range(1, 7):
                TimeSlot.objects.create(
                    timetable=tt,
                    lecture_number=j,
                    start_time=time(9 + j, 0),
                    end_time=time(9 + j, 50)
                )
        
        # Add a Division for the timetable
        div, _ = Division.objects.get_or_create(
            timetable=tt,
            name=f"DIV-{i}"
        )
        all_divisions.append(div)
        
        # Add some dummy entries to show it works
        slots = tt.timeslots.all()
        if tt.entries.count() == 0:
            for day_code, day_name in [('MON', 'Monday'), ('TUE', 'Tuesday')]:
                for s_idx in range(min(3, slots.count())):
                    slot = slots[s_idx]
                    TimetableEntry.objects.create(
                        timetable=tt,
                        day=day_code,
                        timeslot=slot,
                        division=div,
                        subject=random.choice(subjects),
                        faculty=random.choice(teachers),
                        room=random.choice(rooms)
                    )
        
        timetables.append(tt)
    print(f"✅ {len(timetables)} Timetables and {len(all_divisions)} Divisions created")

    # 11. Create 35 Students (STU80001 to STU80035)
    student_pass = "Kv@321321"
    students = []
    blood_groups = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]
    
    student_names = [
        ("Krish", "Patel"), ("Aryan", "Shah"), ("Ishita", "Mehta"), ("Rohan", "Malhotra"), ("Tanisha", "Gupta"),
        ("Vedant", "Kumar"), ("Siya", "Sharma"), ("Kabir", "Singh"), ("Myra", "Desai"), ("Advait", "Verma"),
        ("Ananya", "Reddy"), ("Yash", "Joshi"), ("Zara", "Khan"), ("Vivaan", "Bansal"), ("Saanvi", "Rao"),
        ("Reyansh", "Iyer"), ("Diya", "Pandey"), ("Atharv", "Mishra"), ("Prisha", "Bakshi"), ("Aarav", "Chawla"),
        ("Shanaya", "Saxena"), ("Dhruv", "Kulkarni"), ("Kiara", "Bhatia"), ("Vihaan", "Kapoor"), ("Riya", "Agarwal"),
        ("Ishan", "Singh"), ("Avni", "Grewal"), ("Rudra", "Menon"), ("Mishka", "Prabhu"), ("Ayaan", "Taneja"),
        ("Navya", "Hegde"), ("Krishiv", "Shinde"), ("Amara", "Bhardwaj"), ("Shaurya", "Das"), ("Tanvi", "Chatterjee")
    ]
    
    for i in range(80001, 80036):
        s_username = f"STU{i}"
        idx = i - 80001
        first_name, last_name = student_names[idx]
        
        user, created = User.objects.get_or_create(username=s_username)
        user.set_password(student_pass)
        user.first_name = first_name
        user.last_name = last_name
        user.email = f"{s_username.lower()}@student.ljiet.edu.in"
        user.save()
            
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = 'student'
        profile.institution = inst_name
        profile.phone = fake.phone_number()[:15]
        profile.save()
        
        # Randomly assign dept, branch, course, division
        dept = random.choice(departments)
        branch = random.choice(branches)
        course = random.choice(subjects)
        division = random.choice(all_divisions)
        
        student, created = Student.objects.get_or_create(
            user=user,
            institution=institution,
            defaults={
                'student_id': f"S-ID-{i}",
                'department': dept,
                'branch': branch,
                'course': course,
                'division': division,
                'phone': fake.phone_number()[:15],
                'address': fake.address(),
                'gender': random.choice(['M', 'F']),
                'date_of_birth': fake.date_of_birth(minimum_age=17, maximum_age=22),
                'blood_group': random.choice(blood_groups),
                'parent_name': fake.name(),
                'parent_phone': fake.phone_number()[:15],
                'academic_year': "2024-2025",
                'semester': random.randint(1, 8),
                'gpa': round(random.uniform(5.0, 10.0), 2),
                'status': 'active'
            }
        )
        # If already exists, update details to ensure they are filled
        if not created:
            student.department = dept
            student.branch = branch
            student.course = course
            student.division = division
            student.phone = fake.phone_number()[:15]
            student.address = fake.address()
            student.gender = random.choice(['M', 'F'])
            student.date_of_birth = fake.date_of_birth(minimum_age=17, maximum_age=22)
            student.blood_group = random.choice(blood_groups)
            student.parent_name = fake.name()
            student.parent_phone = fake.phone_number()[:15]
            student.academic_year = "2024-2025"
            student.semester = random.randint(1, 8)
            student.gpa = round(random.uniform(5.0, 10.0), 2)
            student.save()

        students.append(student)
    print(f"✅ {len(students)} Students created with full details")

    # 12. Create 3 News Items
    from institution.models import News
    news_contents = [
        "Welcome to the new academic session at LJIET! We wish all students and faculty a productive year ahead.",
        "Important: The mid-semester examination for SY departments will commence from March 10th, 2026.",
        "LJIET has been awarded the 'Best Innovative Campus' award for 2025. Congratulations to all members!"
    ]
    for content in news_contents:
        News.objects.get_or_create(content=content, institution=institution)
    print(f"✅ 3 News items created")

    # 13. Create 2 Academic Calendars with Details
    from academics.models import AcademicCalendar, CalendarEvent
    from datetime import date, timedelta
    
    cal1, _ = AcademicCalendar.objects.get_or_create(
        semester="Odd Semester",
        year="2025-2026",
        defaults={
            'created_by': admin_user,
            'institution': institution,
            'department': departments[0],
            'shared_with_students': True,
            'shared_with_teachers': True
        }
    )
    
    cal2, _ = AcademicCalendar.objects.get_or_create(
        semester="Even Semester",
        year="2025-2026",
        defaults={
            'created_by': admin_user,
            'institution': institution,
            'department': departments[1],
            'shared_with_students': True,
            'shared_with_teachers': True
        }
    )
    
    # Add events to calendars
    event_list = [
        (cal1, "Semester Start", date(2025, 6, 15), "Regular Teaching"),
        (cal1, "Mid-Term Exam", date(2025, 8, 20), "Test"),
        (cal1, "Diwali Break", date(2025, 11, 1), "Festival Holiday"),
        (cal2, "Semester Reopening", date(2026, 1, 5), "Regular Teaching"),
        (cal2, "Annual Sports Meet", date(2026, 2, 12), "Project / Practical Evaluation"),
        (cal2, "Final Exams", date(2026, 4, 15), "Test")
    ]
    
    for cal, title, dt, etype in event_list:
        CalendarEvent.objects.get_or_create(
            calendar=cal,
            date=dt,
            title=title,
            defaults={'type': etype, 'color_code': CalendarEvent.color_for_type(etype) if hasattr(CalendarEvent, 'color_for_type') else '#2563EB'}
        )
    print(f"✅ 2 Academic Calendars created with events")

    # 14. Enrich Course details
    for subj in subjects:
        subj.description = f"This course {subj.name} ({subj.code}) covers comprehensive topics in {subj.name} for engineering students at LJIET. It includes both theoretical foundations and practical laboratory sessions."
        subj.tuition_fee = 7500.00
        subj.duration_months = 6
        subj.save()
    print(f"✅ All Courses updated with detailed descriptions")

    print("\n🏁 Success! LJIET Dummy Data generation complete.")

if __name__ == "__main__":
    create_ljiet_data()
