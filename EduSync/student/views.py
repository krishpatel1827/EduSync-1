from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Q
from .models import Student
from academics.models import Grade, AcademicCalendar, CalendarEvent
from institution.models import Institution
from accounts.models import UserProfile
from django.db import transaction, IntegrityError
from .forms import StudentCreateForm, StudentEditForm
from generator.models import Timetable, TimetableEntry
from datetime import date


def _find_student_timetable(student):
    """
    Find the best matching active timetable for a student.
    
    Priority hierarchy:
    1. Exact match: department + branch
    2. Department + course match
    3. Any active timetable for the department (fallback)
    4. Institution-wide timetable (no department specified)
    
    Returns: Timetable object or None
    """
    timetable = None
    
    # Priority 1: Exact match - department + branch
    if student.department and student.branch:
        timetable = Timetable.objects.filter(
            department=student.department,
            branch=student.branch,
            is_active=True
        ).first()
    
    # Priority 2: Department + course match
    if not timetable and student.department and student.course:
        timetable = Timetable.objects.filter(
            department=student.department,
            course=student.course,
            is_active=True
        ).first()
    
    # Priority 3: Any active timetable for the same department
    # This is the key change - be more flexible for students without branch/course
    if not timetable and student.department:
        timetable = Timetable.objects.filter(
            department=student.department,
            is_active=True
        ).first()
    
    # Priority 4: Institution-wide timetable (backward compatibility)
    if not timetable:
        timetable = Timetable.objects.filter(
            institution=student.institution,
            department__isnull=True,
            is_active=True
        ).first()
    
    return timetable


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
def student_dashboard(request):
    try:
        student = Student.objects.get(user=request.user)
        grades = Grade.objects.filter(student=student)
        
        # Find matching timetable using helper function
        active_tt = _find_student_timetable(student)
        
        schedule = []
        if active_tt:
            # Get ALL entries for the timetable (not just student's course)
            # This shows the complete timetable with all divisions
            # Filter entries for the student's specific division if assigned
            entry_filter = {'timetable': active_tt}
            if student.division:
                entry_filter['division'] = student.division
            
            entries = TimetableEntry.objects.filter(**entry_filter).select_related(
                'timeslot', 'faculty', 'room', 'division', 'subject'
            ).order_by('timeslot__start_time', 'timeslot__lecture_number')
            
            # Group by day
            days_map = {'MON': 'Monday', 'TUE': 'Tuesday', 'WED': 'Wednesday', 'THU': 'Thursday', 'FRI': 'Friday', 'SAT': 'Saturday', 'SUN': 'Sunday'}
            for day_code, day_name in days_map.items():
                day_entries = [e for e in entries if e.day == day_code]
                if day_entries:
                    schedule.append({
                        'day': day_name,
                        'entries': day_entries
                    })

        # Attendance summary stats
        from academics.models import Attendance
        shared_attendance_records = Attendance.objects.filter(
            student=student,
            sheet__shared_with_students=True,
        )
        shared_attendance_count = shared_attendance_records.count()
        shared_total_attended = sum(r.lectures_attended for r in shared_attendance_records)
        shared_total_lectures = sum(r.total_lectures for r in shared_attendance_records)
        shared_overall_percentage = round((shared_total_attended / shared_total_lectures) * 100, 2) if shared_total_lectures else 0

        # Get upcoming calendar events from shared calendars
        # When a calendar is shared with students, show it to ALL students
        # (department field is informational, not a visibility restriction)
        shared_calendars = AcademicCalendar.objects.filter(shared_with_students=True)
        
        calendar_events = CalendarEvent.objects.filter(
            calendar__in=shared_calendars,
            date__gte=date.today()
        ).order_by('date')[:5]

        context = {
            'student': student,
            'grades': grades,
            'schedule': schedule,
            'timetable': active_tt,
            'shared_attendance_count': shared_attendance_count,
            'shared_total_attended': shared_total_attended,
            'shared_total_lectures': shared_total_lectures,
            'shared_overall_percentage': shared_overall_percentage,
            'calendar_events': calendar_events,
            'shared_calendars': shared_calendars,
        }
        return render(request, 'student/dashboard.html', context)
    except Student.DoesNotExist:
        messages.error(request, 'Student not found.')
        return redirect('landing')

@login_required(login_url='login')
def student_grades(request):
    try:
        student = Student.objects.get(user=request.user)
        grades = Grade.objects.filter(student=student).select_related('course')
        context = {'grades': grades, 'student': student}
        return render(request, 'student/grades.html', context)
    except Student.DoesNotExist:
        return render(request, 'student/grades.html', {'error': 'Student profile not found'})


@ensure_csrf_cookie
@login_required(login_url='login')
def student_list(request):
    institution, error = _get_institution_admin(request)
    if error:
        return render(request, 'student/student_list.html', {'error': error})

    students = Student.objects.filter(institution=institution).select_related(
        'user', 'course', 'department', 'branch', 'division'
    )
    
    # Add timetable availability info for each student
    students_with_tt = []
    for student in students:
        timetable = _find_student_timetable(student)
        students_with_tt.append({
            'student': student,
            'has_timetable': timetable is not None,
            'timetable_name': timetable.name if timetable else None,
        })
    
    return render(request, 'student/student_list.html', {'students_with_tt': students_with_tt})


@login_required(login_url='login')
@never_cache
def student_create(request):
    institution, error = _get_institution_admin(request)
    if error:
        return render(request, 'student/student_form.html', {'error': error})

    if request.method == 'POST':
        form = StudentCreateForm(request.POST, institution=institution)
        if form.is_valid():
            try:
                with transaction.atomic():

                    full_name = form.cleaned_data['name'].strip()
                    parts = full_name.split(None, 1)
                    first_name = parts[0] if parts else full_name
                    last_name = parts[1] if len(parts) > 1 else ""
                    student_id = form.cleaned_data['student_id']
                    username = _unique_username(f"student_{student_id}")
                    password = student_id

                    user = User.objects.create_user(username=username, password=password)
                    user.first_name = first_name
                    user.last_name = last_name
                    user.save()

                    student = Student.objects.create(
                        user=user,
                        institution=institution,
                        student_id=student_id,
                        academic_year=form.cleaned_data.get('academic_year', ''),
                        gender=form.cleaned_data['gender'],
                        date_of_birth=form.cleaned_data.get('date_of_birth'),
                        address=form.cleaned_data.get('address', ''),
                        parent_name=form.cleaned_data.get('parent_name', ''),
                        parent_phone=form.cleaned_data.get('parent_phone', ''),
                        blood_group=form.cleaned_data.get('blood_group', ''),
                        course=form.cleaned_data.get('course'),
                        department=form.cleaned_data.get('department'),
                        division=form.cleaned_data.get('division'),
                    )

                    UserProfile.objects.create(
                        user=student.user,
                        role='student',
                        institution=institution.name
                    )
                messages.success(request, 'Student added successfully.')
                return redirect('student_list')
            except IntegrityError as e:
                messages.error(request, f'Database error: One of the unique fields (like Roll No) might already exist. ({e})')
            except Exception as e:
                messages.error(request, f'An unexpected error occurred: {e}')
    else:
        form = StudentCreateForm(institution=institution)

    return render(request, 'student/student_form.html', {'form': form, 'mode': 'create'})


@login_required(login_url='login')
@never_cache
def student_edit(request, student_id):
    institution, error = _get_institution_admin(request)
    if error:
        return render(request, 'student/student_form.html', {'error': error})

    student = get_object_or_404(Student, id=student_id, institution=institution)

    if request.method == 'POST':
        form = StudentEditForm(request.POST, student=student, institution=institution)
        if form.is_valid():
            full_name = form.cleaned_data['name'].strip()
            parts = full_name.split(None, 1)
            student.user.first_name = parts[0] if parts else full_name
            student.user.last_name = parts[1] if len(parts) > 1 else ''
            student.user.save()

            student.student_id = form.cleaned_data['student_id']
            student.academic_year = form.cleaned_data.get('academic_year', '')
            student.gender = form.cleaned_data['gender']
            student.date_of_birth = form.cleaned_data.get('date_of_birth')
            student.address = form.cleaned_data.get('address', '')
            student.parent_name = form.cleaned_data.get('parent_name', '')
            student.parent_phone = form.cleaned_data.get('parent_phone', '')
            student.blood_group = form.cleaned_data.get('blood_group', '')
            student.course = form.cleaned_data.get('course')
            student.department = form.cleaned_data.get('department')
            student.division = form.cleaned_data.get('division')
            student.save()

            messages.success(request, 'Student updated successfully.')
            return redirect('student_list')
    else:
        form = StudentEditForm(student=student, institution=institution)

    return render(request, 'student/student_form.html', {
        'form': form,
        'mode': 'edit',
        'student': student
    })


@login_required(login_url='login')
def student_delete(request, student_id):
    institution, error = _get_institution_admin(request)
    if error:
        return render(request, 'student/student_list.html', {'error': error})

    student = get_object_or_404(Student, id=student_id, institution=institution)
    user = student.user
    student.delete()
    user.delete()
    messages.success(request, 'Student deleted successfully.')
    return redirect('student_list')

@login_required
def student_timetable(request):
    """
    Renders a premium timetable grid for a specific student.
    Supports Admin/Teacher view via ?student_id=X
    """
    from generator.models import Division, TimetableEntry
    try:
        # 1. Determine Target Student
        student_id = request.GET.get('student_id')
        if student_id and (request.user.userprofile.role in ['institution_admin', 'teacher']):
            student = get_object_or_404(Student, id=student_id)
        else:
            student = Student.objects.get(user=request.user)
            
        institution = student.institution
        
        # 2. Find Active Timetable using helper function
        timetable = _find_student_timetable(student)
            
        if not timetable:
            return render(request, 'student/my_timetable.html', {
                'error': f'Timetable is not generated for {student.department.name if student.department else "your department"}.',
                'student': student,
                'is_admin_view': student.user != request.user
            })

        # Prepare Grid Data
        divisions = Division.objects.filter(timetable=timetable).order_by('name')
        
        # Get slots and handle potential duplicates in data by grouping by (time, type)
        all_raw_slots = list(timetable.timeslots.all().order_by('start_time', 'lecture_number'))
        time_to_slot_ids = {} # Map (time_key) -> list of slot IDs
        all_unique_slots = []
        
        for s in all_raw_slots:
            time_key = (s.start_time, s.end_time, s.is_break)
            if time_key not in time_to_slot_ids:
                time_to_slot_ids[time_key] = [s.id]
                all_unique_slots.append(s)
            else:
                time_to_slot_ids[time_key].append(s.id)
        
        days_map = [
            ('MON', 'Monday'), ('TUE', 'Tuesday'), ('WED', 'Wednesday'),
            ('THU', 'Thursday'), ('FRI', 'Friday'), ('SAT', 'Saturday'), ('SUN', 'Sunday')
        ][:timetable.days_count]
        
        timetable_data = []
        for day_code, day_name in days_map:
            day_slots = []
            for slot in all_unique_slots:
                slot_entries = {}
                time_key = (slot.start_time, slot.end_time, slot.is_break)
                slot_ids = time_to_slot_ids[time_key]
                
                for div in divisions:
                    # Filter: Match Timetable, Day, any matching Slot IDs, and Division
                    entry = TimetableEntry.objects.filter(
                        timetable=timetable,
                        day=day_code,
                        timeslot_id__in=slot_ids,
                        division=div
                    ).select_related('faculty', 'room', 'subject').first()
                    
                    if entry:
                        slot_entries[div.id] = entry
                
                day_slots.append({
                    'slot': slot,
                    'entries': slot_entries
                })
            timetable_data.append({
                'day_code': day_code,
                'day_name': day_name,
                'slots': day_slots
            })

        context = {
            'student': student,
            'divisions': divisions,
            'current_timetable': timetable,
            'timetable_data': timetable_data,
            'semester_text': timetable.footer_semester_text,
            'is_admin_view': student.user != request.user
        }
        return render(request, 'student/my_timetable.html', context)
        
    except (Student.DoesNotExist, UserProfile.DoesNotExist):
        messages.error(request, "Student profile or access context not found.")
        return redirect('landing')


@login_required(login_url='login')
def my_attendance(request):
    """Student view - see shared attendance sheets"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('login')

    from academics.models import Attendance

    attendance_records = Attendance.objects.filter(
        student=student,
        sheet__shared_with_students=True,
    ).select_related('sheet__teacher__user', 'sheet__department').order_by('-sheet__created_at')

    total_attended = sum(r.lectures_attended for r in attendance_records)
    total_lectures = sum(r.total_lectures for r in attendance_records)
    overall_percentage = round((total_attended / total_lectures) * 100, 2) if total_lectures else 0

    context = {
        'student': student,
        'attendance_records': attendance_records,
        'total_attended': total_attended,
        'total_lectures': total_lectures,
        'overall_percentage': overall_percentage,
    }
    return render(request, 'student/my_attendance.html', context)


@login_required(login_url='login')
def student_account_settings(request):
    """Student view - update username and password"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
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
        
        return redirect('student_account_settings')
    
    context = {
        'student': student,
        'user': user,
    }
    return render(request, 'student/account_settings.html', context)
