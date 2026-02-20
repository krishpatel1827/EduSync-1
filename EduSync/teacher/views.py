from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Teacher
from academics.models import Course, AttendanceSheet, AcademicCalendar, CalendarEvent

from student.models import Student
from institution.models import Institution
from accounts.models import UserProfile
from django.db import transaction, IntegrityError
from .forms import TeacherCreateForm, TeacherEditForm
from generator.models import Timetable, TimetableEntry
from datetime import date


def _unique_username(base):
    username = base
    suffix = 1
    while User.objects.filter(username=username).exists():
        username = f"{base}{suffix}"
        suffix += 1
    return username


def _get_institution_admin(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return None, 'User profile not found.'

    if profile.role != 'institution_admin':
        return None, 'Only institution admins can access this page.'

    try:
        institution = Institution.objects.get(admin=request.user)
    except Institution.DoesNotExist:
        return None, 'No institution is linked to this account.'

    return institution, None


@ensure_csrf_cookie
@login_required(login_url='login')
def teacher_dashboard(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
        courses = Course.objects.filter(teachers=teacher)
        
        # Fetch personal schedule from ALL active timetables
        active_tts = Timetable.objects.filter(institution=teacher.institution, is_active=True)
        schedule = []
        if active_tts.exists():
            entries = TimetableEntry.objects.filter(
                faculty=teacher, 
                timetable__in=active_tts
            ).select_related('timeslot', 'subject', 'room', 'division', 'timetable').order_by('timeslot__start_time')
            
            # Group by day
            days_map = {'MON': 'Monday', 'TUE': 'Tuesday', 'WED': 'Wednesday', 'THU': 'Thursday', 'FRI': 'Friday', 'SAT': 'Saturday', 'SUN': 'Sunday'}
            for day_code, day_name in days_map.items():
                day_entries = [e for e in entries if e.day == day_code]
                if day_entries:
                    schedule.append({
                        'day': day_name,
                        'entries': day_entries
                    })

        attendance_archive_count = AttendanceSheet.objects.filter(teacher=teacher).count()

        # Get upcoming calendar events from shared calendars
        # When a calendar is shared with teachers, show it to ALL teachers
        # (department field is informational, not a visibility restriction)
        shared_calendars = AcademicCalendar.objects.filter(shared_with_teachers=True)
        
        calendar_events = CalendarEvent.objects.filter(
            calendar__in=shared_calendars,
            date__gte=date.today()
        ).order_by('date')[:5]

        context = {
            'teacher': teacher,
            'courses': courses,
            'schedule': schedule,
            'attendance_archive_count': attendance_archive_count,
            'has_attendance_archives': attendance_archive_count > 0,
            'calendar_events': calendar_events,
            'shared_calendars': shared_calendars,
        }
        return render(request, 'teacher/dashboard.html', context)
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher not found.')
        return redirect('landing')



@login_required(login_url='login')
def teacher_students(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
        courses = Course.objects.filter(teachers=teacher)
        students = Student.objects.filter(course__in=courses).distinct()
        context = {'students': students, 'teacher': teacher}
        return render(request, 'teacher/students.html', context)
    except Teacher.DoesNotExist:
        return render(request, 'teacher/students.html', {'error': 'Teacher profile not found'})


@ensure_csrf_cookie
@login_required(login_url='login')
def teacher_list(request):
    institution, error = _get_institution_admin(request)
    if error:
        return render(request, 'teacher/teacher_list.html', {'error': error})

    teachers = Teacher.objects.filter(institution=institution).select_related('user')
    return render(request, 'teacher/teacher_list.html', {'teachers': teachers})


@login_required(login_url='login')
@never_cache
def teacher_create(request):
    institution, error = _get_institution_admin(request)
    if error:
        return render(request, 'teacher/teacher_form.html', {'error': error})

    if request.method == 'POST':
        form = TeacherCreateForm(request.POST, request.FILES, institution=institution)
        if form.is_valid():
            try:
                with transaction.atomic():

                    full_name = form.cleaned_data['name'].strip()
                    parts = full_name.split(None, 1)
                    first_name = parts[0] if parts else full_name
                    last_name = parts[1] if len(parts) > 1 else ""
                    employee_id = form.cleaned_data['employee_id']
                    username = _unique_username(f"teacher_{employee_id}")
                    password = employee_id

                    user = User.objects.create_user(username=username, password=password)
                    user.first_name = first_name
                    user.last_name = last_name
                    user.save()

                    teacher = Teacher.objects.create(
                        user=user,
                        institution=institution,
                        employee_id=employee_id,
                        department=form.cleaned_data['department'],
                        qualification=form.cleaned_data['qualification'],
                        gender=form.cleaned_data['gender'],
                        date_of_birth=form.cleaned_data.get('date_of_birth'),
                        phone=form.cleaned_data.get('phone', ''),
                        address=form.cleaned_data.get('address', ''),
                        salary=form.cleaned_data.get('salary', 0.00),
                        contract_type=form.cleaned_data['contract_type'],
                        photo=form.cleaned_data.get('photo'),
                    )

                    courses = form.cleaned_data.get('courses')
                    if courses:
                        for course in courses:
                            course.teachers.add(teacher)

                    UserProfile.objects.create(
                        user=teacher.user,
                        role='teacher',
                        institution=institution.name
                    )
                messages.success(request, 'Teacher added successfully.')
                return redirect('teacher_list')
            except IntegrityError as e:
                messages.error(request, f'Database error: One of the unique fields (like Employee ID) might already exist. ({e})')
            except Exception as e:
                messages.error(request, f'An unexpected error occurred: {e}')
    else:
        form = TeacherCreateForm(institution=institution)

    return render(request, 'teacher/teacher_form.html', {'form': form, 'mode': 'create'})


@login_required(login_url='login')
@never_cache
def teacher_edit(request, teacher_id):
    institution, error = _get_institution_admin(request)
    if error:
        return render(request, 'teacher/teacher_form.html', {'error': error})

    teacher = get_object_or_404(Teacher, id=teacher_id, institution=institution)

    if request.method == 'POST':
        form = TeacherEditForm(request.POST, request.FILES, teacher=teacher, institution=institution)
        if form.is_valid():
            full_name = form.cleaned_data['name'].strip()
            parts = full_name.split(None, 1)
            teacher.user.first_name = parts[0] if parts else full_name
            teacher.user.last_name = parts[1] if len(parts) > 1 else ''
            teacher.user.save()

            teacher.employee_id = form.cleaned_data['employee_id']
            teacher.department = form.cleaned_data['department']
            teacher.qualification = form.cleaned_data['qualification']
            teacher.gender = form.cleaned_data['gender']
            teacher.date_of_birth = form.cleaned_data.get('date_of_birth')
            teacher.phone = form.cleaned_data.get('phone', '')
            teacher.address = form.cleaned_data.get('address', '')
            teacher.salary = form.cleaned_data.get('salary', 0.00)
            teacher.contract_type = form.cleaned_data['contract_type']

            if form.cleaned_data.get('photo'):
                teacher.photo = form.cleaned_data.get('photo')
            teacher.save()

            selected_courses = set(form.cleaned_data.get('courses', []))
            current_courses = set(Course.objects.filter(teachers=teacher))

            for course in current_courses - selected_courses:
                course.teachers.remove(teacher)
            for course in selected_courses - current_courses:
                course.teachers.add(teacher)

            return redirect('teacher_list')
    else:
        form = TeacherEditForm(teacher=teacher, institution=institution)

    return render(request, 'teacher/teacher_form.html', {
        'form': form,
        'mode': 'edit',
        'teacher': teacher
    })


@login_required(login_url='login')
def teacher_delete(request, teacher_id):
    institution, error = _get_institution_admin(request)
    if error:
        return render(request, 'teacher/teacher_list.html', {'error': error})

    teacher = get_object_or_404(Teacher, id=teacher_id, institution=institution)
    user = teacher.user
    teacher.delete()
    user.delete()
    messages.success(request, 'Teacher deleted successfully.')
    return redirect('teacher_list')


# ═══ ATTENDANCE GENERATOR ═══

@login_required(login_url='login')
def attendance_generator(request):
    """Teacher attendance generator page - step 1"""
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('login')

    # Get departments for this teacher's institution
    from institution.models import Department
    departments = Department.objects.filter(institution=teacher.institution).order_by('name')

    if request.method == 'POST':
        dept_id = request.POST.get('department_id')
        date_from = request.POST.get('date_from')
        date_to = request.POST.get('date_to')
        total_lectures = request.POST.get('total_lectures')

        if not all([dept_id, date_from, date_to, total_lectures]):
            messages.error(request, 'Please fill all fields.')
            return render(request, 'teacher/attendance_generator.html', {'departments': departments})

        try:
            total_lectures = int(total_lectures)
            if total_lectures <= 0:
                raise ValueError("Total lectures must be positive")
        except ValueError:
            messages.error(request, 'Total lectures must be a positive number.')
            return render(request, 'teacher/attendance_generator.html', {'departments': departments})

        # Redirect to attendance sheet with parameters
        return redirect('attendance_sheet', dept_id=dept_id, date_from=date_from, date_to=date_to, total_lectures=total_lectures)

    context = {
        'teacher': teacher,
        'departments': departments,
    }
    return render(request, 'teacher/attendance_generator.html', context)


@login_required(login_url='login')
def attendance_archives(request):
    """Teacher attendance archives list"""
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('login')

    sheets = AttendanceSheet.objects.filter(teacher=teacher).select_related('department').order_by('-created_at')

    context = {
        'teacher': teacher,
        'sheets': sheets,
    }
    return render(request, 'teacher/attendance_archives.html', context)


@login_required(login_url='login')
def attendance_sheet(request, dept_id, date_from, date_to, total_lectures):
    """Generate and display attendance sheet for students"""
    from academics.models import AttendanceSheet as Sheet, Attendance
    from institution.models import Department
    from student.models import Student
    from datetime import datetime

    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('login')

    try:
        department = Department.objects.get(id=dept_id, institution=teacher.institution)
    except Department.DoesNotExist:
        messages.error(request, 'Department not found.')
        return redirect('attendance_generator')

    # Parse dates
    try:
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Invalid date format.')
        return redirect('attendance_generator')

    total_lectures = int(total_lectures)

    # Get or create AttendanceSheet
    sheet, created = Sheet.objects.get_or_create(
        teacher=teacher,
        department=department,
        date_from=date_from_obj,
        date_to=date_to_obj,
        defaults={'total_lectures': total_lectures}
    )
    if sheet.total_lectures != total_lectures:
        sheet.total_lectures = total_lectures
        sheet.save(update_fields=['total_lectures', 'updated_at'])

    # Get students in this department
    students = Student.objects.filter(
        department=department,
        institution=teacher.institution
    ).select_related('user').order_by('student_id')

    # Optimized: Get or create attendance records efficiently
    existing_records = Attendance.objects.filter(sheet=sheet, student__in=students)
    existing_students = {r.student_id for r in existing_records}
    
    records_to_create = []
    records_to_update = []
    
    for student in students:
        if student.id not in existing_students:
            records_to_create.append(Attendance(
                sheet=sheet,
                student=student,
                total_lectures=total_lectures,
                lectures_attended=0
            ))
    
    if records_to_create:
        Attendance.objects.bulk_create(records_to_create)
    
    # Update existing records if total_lectures changed
    existing_records.exclude(total_lectures=total_lectures).update(total_lectures=total_lectures)

    # Get attendance records
    attendance_records = Attendance.objects.filter(sheet=sheet).select_related('student__user').order_by('student__student_id')

    if request.method == 'POST':
        # Update attendance records
        for record in attendance_records:
            lectures_attended = request.POST.get(f'lectures_attended_{record.id}')
            if lectures_attended is not None:
                try:
                    attended = int(lectures_attended)
                    if 0 <= attended <= record.total_lectures:
                        record.lectures_attended = attended
                        record.save()
                except ValueError:
                    pass

        action = request.POST.get('action', 'save')
        if action == 'share':
            sheet.shared_with_students = True
            sheet.save(update_fields=['shared_with_students', 'updated_at'])
            messages.success(request, 'Attendance saved and shared with students.')
        elif action == 'unshare':
            sheet.shared_with_students = False
            sheet.save(update_fields=['shared_with_students', 'updated_at'])
            messages.success(request, 'Attendance saved and unshared from students.')
        else:
            messages.success(request, 'Attendance saved.')

        return redirect('teacher_dashboard')

    context = {
        'teacher': teacher,
        'sheet': sheet,
        'department': department,
        'attendance_records': attendance_records,
        'total_lectures': total_lectures,
    }
    return render(request, 'teacher/attendance_sheet.html', context)


# ═══ MARKS GENERATOR ═══
@login_required(login_url='login')
def generate_marks(request):
    """Teacher marks generator - select department to generate marks for"""
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('login')

    # Get departments available to this teacher (their department primarily)
    departments = []
    if teacher.department:
        departments = [teacher.department]
    else:
        # If no department, get all departments from institution
        from institution.models import Department
        departments = list(Department.objects.filter(institution=teacher.institution))

    if request.method == 'POST':
        dept_id = request.POST.get('department')
        if not dept_id:
            messages.error(request, 'Please select a department.')
            return render(request, 'teacher/marks_generator.html', {'departments': departments, 'teacher': teacher})

        # Ensure department belongs to teacher's institution
        try:
            from institution.models import Department
            department = Department.objects.get(id=dept_id, institution=teacher.institution)
        except Department.DoesNotExist:
            messages.error(request, 'Department not found.')
            return render(request, 'teacher/marks_generator.html', {'departments': departments, 'teacher': teacher})

        # Redirect to marks entry sheet
        return redirect('marks_entry_sheet', dept_id=dept_id)

    context = {
        'teacher': teacher,
        'departments': departments,
    }
    return render(request, 'teacher/marks_generator.html', context)


@login_required(login_url='login')
def marks_entry_sheet(request, dept_id):
    """Generate and display marks entry sheet for students in a department"""
    from institution.models import Department
    from student.models import Student
    from marksheet.models import Marksheet, Marks
    from datetime import date

    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('login')

    try:
        department = Department.objects.get(id=dept_id, institution=teacher.institution)
    except Department.DoesNotExist:
        messages.error(request, 'Department not found.')
        return redirect('generate_marks')

    # Get students in this department
    students = Student.objects.filter(
        department=department,
        institution=teacher.institution
    ).select_related('user').order_by('student_id')

    # Get semester from request or use current semester calculation
    current_year = date.today().year
    current_month = date.today().month
    semester = 1 if current_month < 7 else 2
    academic_year = f"{current_year}-{current_year + 1}"

    # Optimized: Get or create marksheets for all students efficiently
    existing_marksheets = Marksheet.objects.filter(
        student__in=[s.user for s in students],
        semester=semester,
        academic_year=academic_year
    ).select_related('student')
    
    existing_user_ids = {m.student_id for m in existing_marksheets}
    marksheets_to_create = []
    
    for student in students:
        if student.user_id not in existing_user_ids:
            marksheets_to_create.append(Marksheet(
                student=student.user,
                semester=semester,
                academic_year=academic_year,
                teacher=teacher.user,
                department=department,
                shared_with_students=False
            ))
            
    if marksheets_to_create:
        Marksheet.objects.bulk_create(marksheets_to_create)
        # Re-fetch to get IDs
        existing_marksheets = Marksheet.objects.filter(
            student__in=[s.user for s in students],
            semester=semester,
            academic_year=academic_year
        )
    
    marksheets = {m.student_id: m for m in existing_marksheets}

    if request.method == 'POST':
        # Update marks for all students
        for student in students:
            marksheet = marksheets[student.id]
            
            # Get marks for each course/subject
            courses = Course.objects.filter(institution=teacher.institution)
            for course in courses:
                marks_value = request.POST.get(f'marks_{student.id}_{course.id}')
                if marks_value and marks_value.strip():
                    try:
                        marks_int = int(marks_value)
                        if 0 <= marks_int <= 100:
                            Marks.objects.update_or_create(
                                marksheet=marksheet,
                                subject=course,
                                defaults={'marks': marks_int}
                            )
                    except (ValueError, TypeError):
                        pass

            # Recalculate marksheet statistics
            marksheet.calculate_stats()

        action = request.POST.get('action', 'save')
        if action == 'publish':
            # Mark all marksheets as shared with students
            for student in students:
                marksheet = marksheets[student.id]
                marksheet.shared_with_students = True
                marksheet.save(update_fields=['shared_with_students', 'updated_at'])
            messages.success(request, 'Marks saved and published to students.')
        elif action == 'unpublish':
            # Unshare marksheets from students
            for student in students:
                marksheet = marksheets[student.id]
                marksheet.shared_with_students = False
                marksheet.save(update_fields=['shared_with_students', 'updated_at'])
            messages.success(request, 'Marks saved and unpublished from students.')
        else:
            messages.success(request, 'Marks saved.')

        return redirect('teacher_dashboard')

    # Get all courses for this institution
    courses = Course.objects.filter(institution=teacher.institution)

    # Optimized: Fetch all marks in a single query
    all_marks = Marks.objects.filter(marksheet__in=marksheets.values()).select_related('subject')
    marks_lookup = {}
    for mark in all_marks:
        marks_lookup[(mark.marksheet_id, mark.subject_id)] = mark.marks

    # Prepare data for template
    student_marks_data = []
    for student in students:
        marksheet = marksheets.get(student.user_id)
        marks_dict = {}
        if marksheet:
            for course in courses:
                marks_dict[course.id] = marks_lookup.get((marksheet.id, course.id), '')
        
        student_marks_data.append({
            'student': student,
            'marksheet': marksheet,
            'marks': marks_dict
        })

    context = {
        'teacher': teacher,
        'department': department,
        'students': student_marks_data,
        'courses': courses,
        'semester': semester,
        'academic_year': academic_year,
    }
    return render(request, 'teacher/marks_entry_sheet.html', context)


# ═══ TEACHER ACCOUNT SETTINGS ═══

@login_required(login_url='login')
def teacher_account_settings(request):
    """Teacher view - update username and password"""
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('login')
    
    user = request.user
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_username':
            new_username = request.POST.get('new_username', '').strip()
            if new_username:
                if User.objects.filter(username=new_username).exclude(pk=user.pk).exists():
                    messages.error(request, 'This username is already taken.')
                elif len(new_username) < 3:
                    messages.error(request, 'Username must be at least 3 characters.')
                elif not new_username.isalnum() and '_' not in new_username:
                    messages.error(request, 'Username can only contain letters, numbers, and underscores.')
                else:
                    user.username = new_username
                    user.save()
                    messages.success(request, 'Username updated successfully!')
            else:
                messages.error(request, 'Please enter a valid username.')
        
        elif action == 'update_password':
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')
            
            if not user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
            elif len(new_password) < 8:
                messages.error(request, 'New password must be at least 8 characters.')
            elif new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
            else:
                user.set_password(new_password)
                user.save()
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)
                messages.success(request, 'Password updated successfully!')
        
        return redirect('teacher_account_settings')
    
    context = {
        'teacher': teacher,
        'user': user,
    }
    return render(request, 'teacher/account_settings.html', context)
