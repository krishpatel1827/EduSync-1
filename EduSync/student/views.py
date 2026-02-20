# ================================================================================
# STUDENT APP - VIEWS.PY
# ================================================================================
# This file contains all the view functions for student management in EduSync.
# It handles student dashboards, academic information display, account management,
# and administrative functions for managing student records.
#
# WHAT ARE VIEWS IN DJANGO?
# Views are Python functions that handle HTTP requests and return HTTP responses.
# They contain the business logic that processes data and renders templates.
# Each view function corresponds to a URL and handles specific user interactions.
#
# STUDENT SYSTEM FUNCTIONALITY:
# 1. Student Dashboard: Personal academic information hub
# 2. Grade Viewing: Academic performance and transcript data  
# 3. Timetable Display: Class schedules and timing information
# 4. Attendance Tracking: Attendance records and statistics
# 5. Account Management: Username/password updates
# 6. Admin Functions: Creating, editing, and managing student records
#
# USER ROLES & ACCESS:
# - Students: Access to their own dashboard, grades, timetable, attendance
# - Institution Admins: Full access to all student management functions
# - Teachers: Limited access to view student information for their classes
#
# SECURITY MEASURES:
# - @login_required: Ensures only authenticated users can access views
# - Role-based access control: Different permissions for different user types
# - CSRF protection: Prevents cross-site request forgery attacks
# - Institution isolation: Users can only see data from their own institution
# ================================================================================

# Import Django core functionality
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db import transaction, IntegrityError
from datetime import date

# Import models from different apps
from .models import Student
from academics.models import Grade, AcademicCalendar, CalendarEvent, Attendance
from institution.models import Institution
from accounts.models import UserProfile
from generator.models import Timetable, TimetableEntry

# Import form classes for student data collection
from .forms import StudentCreateForm, StudentEditForm


def _find_student_timetable(student):
    """
    HELPER FUNCTION: Find the best matching active timetable for a student
    
    WHAT THIS FUNCTION DOES:
    Attempts to locate an active timetable for a student using a priority hierarchy.
    This ensures students see appropriate class schedules based on their academic assignment.
    
    PRIORITY HIERARCHY (most specific to most general):
    1. Exact match: Same department AND same branch (most specific)
    2. Department + course match: Same department AND same course  
    3. Any active timetable for the department (fallback for broad matching)
    4. Institution-wide timetable: No department specified (global fallback)
    
    WHY THIS PRIORITY SYSTEM?
    - Students should see the most relevant timetable for their specific program
    - Fallbacks ensure students always see some timetable if available
    - Handles cases where students might not have all assignments (branch, course)
    
    PARAMETERS:
    student (Student): The student object to find a timetable for
    
    RETURNS:
    Timetable object if found, None if no matching timetable exists
    
    USAGE EXAMPLES:
    - CS student in CS department with CS branch → Gets CS-specific timetable
    - Student in Engineering department without branch → Gets any Engineering timetable
    - New student with only institution → Gets institution-wide timetable
    """
    timetable = None
    
    # Priority 1: Exact match - department + branch (most specific)
    # Example: Computer Science student gets Computer Science timetable
    if student.department and student.branch:
        timetable = Timetable.objects.filter(
            department=student.department,  # Must match student's department
            branch=student.branch,          # Must match student's branch
            is_active=True                  # Only active timetables
        ).first()  # Get the first matching timetable
    
    # Priority 2: Department + course match (specific but broader than branch)
    # Example: Engineering student gets timetable for their specific course
    if not timetable and student.department and student.course:
        timetable = Timetable.objects.filter(
            department=student.department,  # Must match student's department
            course=student.course,          # Must match student's course
            is_active=True                  # Only active timetables
        ).first()
    
    # Priority 3: Any active timetable for the same department (flexible fallback)
    # This is key for students who don't have branch/course assignments yet
    # Example: New student in Engineering gets any active Engineering timetable
    if not timetable and student.department:
        timetable = Timetable.objects.filter(
            department=student.department,  # Must match student's department
            is_active=True                  # Only active timetables
        ).first()  # Accept any timetable for the department
    
    # Priority 4: Institution-wide timetable (global fallback for backward compatibility)
    # Example: Student gets general institution timetable if no specific one exists
    if not timetable:
        timetable = Timetable.objects.filter(
            institution=student.institution,  # Must match student's institution
            department__isnull=True,         # No specific department (institution-wide)
            is_active=True                   # Only active timetables
        ).first()
    
    return timetable


def _unique_username(base):
    """
    HELPER FUNCTION: Generate a unique username based on a base string
    
    WHAT THIS FUNCTION DOES:
    Takes a base username (e.g., "student_ST001") and ensures it's unique by
    adding number suffixes if the base username already exists.
    
    LOGIC:
    1. Start with the base username
    2. Check if it exists in the database
    3. If it exists, add a number suffix (1, 2, 3, etc.)
    4. Keep incrementing until we find a unique username
    
    PARAMETERS:
    base (str): The base username to make unique (e.g., "student_ST001")
    
    RETURNS:
    str: A guaranteed unique username
    
    EXAMPLES:
    - Input: "student_ST001", Output: "student_ST001" (if available)
    - Input: "student_ST001", Output: "student_ST0011" (if ST001 exists)
    - Input: "student_ST001", Output: "student_ST0012" (if ST001 and ST0011 exist)
    
    WHY THIS IS NEEDED:
    - Prevents database integrity errors when creating user accounts
    - Ensures every student gets a unique login username
    - Handles cases where student IDs might be reused or duplicated
    """
    username = base                    # Start with the base username
    suffix = 1                        # Start numbering from 1
    
    # Keep checking and incrementing until we find a unique username
    while User.objects.filter(username=username).exists():
        username = f"{base}{suffix}"   # Add number suffix to base
        suffix += 1                   # Increment for next attempt
    
    return username                   # Return the unique username


def _get_institution_admin(request):
    """
    HELPER FUNCTION: Validate and retrieve institution admin information
    
    WHAT THIS FUNCTION DOES:
    Validates that the current user is an institution admin and returns their
    associated institution. This is used to secure admin-only functions.
    
    VALIDATION STEPS:
    1. Check if user has a UserProfile (account setup completed)
    2. Verify user's role is 'institution_admin' 
    3. Find the Institution object where this user is the admin
    4. Return institution or appropriate error message
    
    PARAMETERS:
    request: Django HTTP request object containing user information
    
    RETURNS:
    tuple: (Institution object, Error message)
    - Success: (Institution, None)
    - Failure: (None, "Error description")
    
    USAGE:
    institution, error = _get_institution_admin(request)
    if error:
        return render(request, 'template.html', {'error': error})
    
    SECURITY PURPOSE:
    - Prevents non-admin users from accessing admin functions
    - Ensures admins can only manage their own institution's data
    - Provides consistent error handling across admin views
    """
    try:
        # Try to get the user's profile information
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        # User doesn't have a profile - account setup incomplete
        return None, 'User profile not found.'

    # Check if user has admin privileges
    if profile.role != 'institution_admin':
        return None, 'Only institution admins can access this page.'

    try:
        # Find the institution where this user is the admin
        institution = Institution.objects.get(admin=request.user)
    except Institution.DoesNotExist:
        # User is marked as admin but no institution is linked
        return None, 'No institution is linked to this account.'

    # Success - return the institution
    return institution, None


@ensure_csrf_cookie
@login_required(login_url='login')
def student_dashboard(request):
    """
    MAIN VIEW: Student personal dashboard displaying academic information
    
    WHAT THIS VIEW DOES:
    Creates a comprehensive dashboard for students showing their grades, timetable,
    attendance records, and upcoming calendar events. This is the main hub where
    students access all their academic information.
    
    DASHBOARD COMPONENTS:
    1. Student Profile: Basic student information and status
    2. Grades: Academic performance and course results
    3. Timetable: Weekly class schedule (if available)
    4. Attendance: Attendance statistics from shared records
    5. Calendar Events: Upcoming academic events and important dates
    
    TIMETABLE DISPLAY LOGIC:
    - Uses _find_student_timetable() to find matching timetable
    - Shows complete timetable if student has division assignment
    - Groups entries by day of week for organized display
    - Handles cases where no timetable is available
    
    ATTENDANCE CALCULATIONS:
    - Only shows attendance from sheets shared with students
    - Calculates overall attendance percentage across all subjects
    - Provides summary statistics for quick overview
    
    CALENDAR INTEGRATION:
    - Shows upcoming events from calendars shared with students
    - Filters events to show only future dates
    - Limits to 5 most immediate events to avoid clutter
    
    ACCESS CONTROL:
    - @ensure_csrf_cookie: Enables CSRF protection for forms
    - @login_required: Only authenticated users can access
    - Automatically redirects non-students to landing page
    
    ERROR HANDLING:
    - Gracefully handles missing student profiles
    - Provides user-friendly error messages
    - Redirects to appropriate pages on errors
    """
    try:
        # Get the student record for the current user
        student = Student.objects.get(user=request.user)
        
        # Get all grades for this student
        grades = Grade.objects.filter(student=student)
        
        # Find matching timetable using helper function
        active_tt = _find_student_timetable(student)
        
        # Initialize empty schedule
        schedule = []
        
        if active_tt:
            # Build the timetable schedule for display
            
            # Prepare filter criteria for timetable entries
            entry_filter = {'timetable': active_tt}
            
            # If student has a specific division, show only their entries
            # Otherwise, show all entries for the timetable
            if student.division:
                entry_filter['division'] = student.division
            
            # Get timetable entries with related data for efficiency
            entries = TimetableEntry.objects.filter(**entry_filter).select_related(
                'timeslot',   # Time information
                'faculty',    # Teacher information  
                'room',       # Location information
                'division',   # Student group information
                'subject'     # Course information
            ).order_by('timeslot__start_time', 'timeslot__lecture_number')
            
            # Group entries by day of the week for organized display
            days_map = {
                'MON': 'Monday', 'TUE': 'Tuesday', 'WED': 'Wednesday', 
                'THU': 'Thursday', 'FRI': 'Friday', 'SAT': 'Saturday', 'SUN': 'Sunday'
            }
            
            # Create daily schedule structure
            for day_code, day_name in days_map.items():
                # Filter entries for this specific day
                day_entries = [e for e in entries if e.day == day_code]
                
                # Only include days that have classes scheduled
                if day_entries:
                    schedule.append({
                        'day': day_name,      # Human-readable day name
                        'entries': day_entries # List of classes for this day
                    })

        # Calculate attendance statistics from shared attendance sheets
        # Only show attendance that teachers have chosen to share with students
        shared_attendance_records = Attendance.objects.filter(
            student=student,                      # This specific student
            sheet__shared_with_students=True,     # Only shared attendance sheets
        )
        
        # Calculate summary statistics
        shared_attendance_count = shared_attendance_records.count()
        shared_total_attended = sum(r.lectures_attended for r in shared_attendance_records)
        shared_total_lectures = sum(r.total_lectures for r in shared_attendance_records)
        
        # Calculate overall attendance percentage with division by zero protection
        if shared_total_lectures > 0:
            shared_overall_percentage = round((shared_total_attended / shared_total_lectures) * 100, 2)
        else:
            shared_overall_percentage = 0

        # Get upcoming calendar events from shared calendars
        # When a calendar is shared with students, all students can see it
        # (department field is informational, not a visibility restriction)
        shared_calendars = AcademicCalendar.objects.filter(shared_with_students=True)
        
        # Get next 5 upcoming events for dashboard display
        calendar_events = CalendarEvent.objects.filter(
            calendar__in=shared_calendars,    # From shared calendars only
            date__gte=date.today()           # Only future events
        ).order_by('date')[:5]               # Limit to 5 most immediate events

        # Prepare all data for template rendering
        context = {
            'student': student,                              # Student profile information
            'grades': grades,                                # Academic grades and courses
            'schedule': schedule,                            # Weekly timetable schedule
            'timetable': active_tt,                         # Timetable object (for additional info)
            'shared_attendance_count': shared_attendance_count,     # Number of attendance records
            'shared_total_attended': shared_total_attended,  # Total classes attended
            'shared_total_lectures': shared_total_lectures,  # Total classes conducted
            'shared_overall_percentage': shared_overall_percentage, # Overall attendance %
            'calendar_events': calendar_events,              # Upcoming academic events
            'shared_calendars': shared_calendars,            # Available calendars
            'semester_text': f"Semester {student.semester}", # Current semester display text
        }
        
        # Render the dashboard template with all prepared data
        return render(request, 'student/dashboard.html', context)
        
    except Student.DoesNotExist:
        # Handle case where user is authenticated but not a student
        messages.error(request, 'Student not found.')
        return redirect('landing')  # Redirect to main page

@login_required(login_url='login')
def student_grades(request):
    """
    Redirects to the new marksheet application view
    """
    return redirect('student_marksheet')


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
                        semester=form.cleaned_data.get('semester', 1),
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
            student.semester = form.cleaned_data.get('semester', 1)
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
