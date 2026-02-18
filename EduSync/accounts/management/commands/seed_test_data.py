"""
Management command to seed test data for production.
Creates institution, departments, teachers, students, etc.
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from institution.models import Institution, Department, StudyYear
from teacher.models import Teacher
from student.models import Student
from academics.models import Course


class Command(BaseCommand):
    help = 'Seed test data for the application'

    def handle(self, *args, **options):
        # Check if we should seed (controlled by env var)
        if os.environ.get('SKIP_SEED', 'false').lower() == 'true':
            self.stdout.write(self.style.WARNING('SKIP_SEED=true, skipping seed.'))
            return

        # Check if already seeded (institution exists)
        if Institution.objects.exists():
            self.stdout.write(self.style.SUCCESS('Data already exists. Skipping seed.'))
            return

        self.stdout.write('Seeding test data...')

        # Create Institution
        institution = Institution.objects.create(
            name='Prestige Academy',
            address='123 Education Street, Knowledge City',
            contact_email='admin@prestigeacademy.edu',
            contact_phone='1234567890',
            website='https://prestigeacademy.edu'
        )
        self.stdout.write(self.style.SUCCESS(f'Created institution: {institution.name}'))

        # Create Departments
        departments_data = [
            ('Computer Science', 'CS'),
            ('Mathematics', 'MATH'),
            ('Physics', 'PHY'),
            ('English', 'ENG'),
        ]
        departments = {}
        for name, code in departments_data:
            dept = Department.objects.create(
                name=name,
                code=code,
                institution=institution
            )
            departments[code] = dept
            self.stdout.write(f'  Created department: {name}')

        # Create Study Years
        study_years = {}
        for dept_code, dept in departments.items():
            for year in range(1, 5):
                sy = StudyYear.objects.create(
                    name=f'Year {year}',
                    year_number=year,
                    department=dept
                )
                study_years[f'{dept_code}_Y{year}'] = sy

        self.stdout.write(self.style.SUCCESS('Created study years'))

        # Create Courses
        courses_data = [
            ('Introduction to Programming', 'CS101', 'CS', 1),
            ('Data Structures', 'CS201', 'CS', 2),
            ('Algorithms', 'CS301', 'CS', 3),
            ('Calculus I', 'MATH101', 'MATH', 1),
            ('Linear Algebra', 'MATH201', 'MATH', 2),
            ('Mechanics', 'PHY101', 'PHY', 1),
            ('English Composition', 'ENG101', 'ENG', 1),
        ]
        courses = {}
        for name, code, dept_code, year in courses_data:
            course = Course.objects.create(
                name=name,
                code=code,
                department=departments[dept_code],
                study_year=study_years[f'{dept_code}_Y{year}'],
                credits=3
            )
            courses[code] = course

        self.stdout.write(self.style.SUCCESS('Created courses'))

        # Create 10 Teachers
        for i in range(1, 11):
            username = f'teacher{i:02d}'
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=f'{username}@prestigeacademy.edu',
                    password='123',
                    first_name=f'Teacher',
                    last_name=f'{i:02d}'
                )
                dept_code = list(departments.keys())[(i - 1) % len(departments)]
                Teacher.objects.create(
                    user=user,
                    institution=institution,
                    department=departments[dept_code],
                    employee_id=f'T{i:03d}',
                    phone=f'555000{i:04d}',
                    specialization='General'
                )

        self.stdout.write(self.style.SUCCESS('Created 10 teachers (teacher01-teacher10, password: 123)'))

        # Create 10 Students
        for i in range(1, 11):
            username = f'student{i:02d}'
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=f'{username}@student.prestigeacademy.edu',
                    password='123',
                    first_name=f'Student',
                    last_name=f'{i:02d}'
                )
                dept_code = list(departments.keys())[(i - 1) % len(departments)]
                year_num = ((i - 1) % 4) + 1
                Student.objects.create(
                    user=user,
                    institution=institution,
                    department=departments[dept_code],
                    study_year=study_years[f'{dept_code}_Y{year_num}'],
                    enrollment_number=f'S{i:03d}',
                    phone=f'555100{i:04d}'
                )

        self.stdout.write(self.style.SUCCESS('Created 10 students (student01-student10, password: 123)'))

        self.stdout.write(self.style.SUCCESS('\n=== SEED COMPLETE ==='))
        self.stdout.write('Login credentials:')
        self.stdout.write('  Teachers: teacher01 to teacher10 (password: 123)')
        self.stdout.write('  Students: student01 to student10 (password: 123)')
