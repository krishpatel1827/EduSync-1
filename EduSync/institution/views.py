# ================================================================================
# INSTITUTION APP - VIEWS.PY
# ================================================================================
# This file contains all the view functions that handle institution management,
# admin dashboards, department management, and portal access functionality.
#
# WHAT IS THE INSTITUTION APP?
# The institution app manages the core entity of EduSync - the educational institution.
# It handles everything related to the institution as a whole, including:
# - Institution dashboard and overview
# - Department and branch management  
# - News and announcements system
# - Room management for classrooms
# - Academic calendar management
# - Portal login system for role switching
#
# KEY CONCEPTS:
# - Institution: The main entity (school, college, university)
# - Admin: The person who manages the entire institution  
# - Portal Access: System allowing admins to access teacher/student views
# - Multi-tenant: Each institution's data is completely separate from others
# ================================================================================

# Import necessary Django functions and decorators
from django.shortcuts import render, redirect, get_object_or_404  # View helper functions
from django.contrib.auth import login, logout  # Authentication functions
from django.contrib import messages  # User notification system
from django.contrib.auth.decorators import login_required  # Decorator to require authentication
from django.views.decorators.cache import never_cache  # Prevent caching for security
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect  # CSRF protection

# Import models from various apps
from .models import Institution, News, Department, AcademicCalendarEvent  # Institution app models
from academics.models import Course, Branch  # Academic structure models
from teacher.models import Teacher  # Faculty management
from student.models import Student  # Student management  
from generator.models import Room  # Classroom management
from datetime import date  # For handling dates in calendar system


# ================================================================================
# INSTITUTION DASHBOARD SYSTEM
# ================================================================================

@ensure_csrf_cookie  # Ensures CSRF token is available for any forms
@csrf_protect  # Validates CSRF token for form submissions
@never_cache  # Prevents browser from caching this sensitive page
@login_required(login_url='login')  # Redirects to login page if user not authenticated
def dashboard_view(request):
    """
    WHAT THIS FUNCTION DOES:
    Displays the main institution dashboard showing overview of all institution data.
    This is like a "control panel" for institution administrators.
    
    PARAMETERS:
    - request: Django HttpRequest object containing user session and request data
    
    RETURN VALUE:
    HttpResponse containing the rendered dashboard template with context data
    
    BUSINESS LOGIC:
    1. Find the institution associated with the logged-in admin user
    2. Gather overview data (news, courses, teachers) for display
    3. Pass all data to the dashboard template for rendering
    
    WHO CAN ACCESS THIS:
    Only authenticated users who are institution administrators.
    The @login_required decorator ensures only logged-in users can access this.
    
    DATA DISPLAYED:
    - Institution information (name, contact details, etc.)
    - Recent news and announcements
    - Course offerings and statistics
    - Teacher roster and information
    - Quick access navigation links
    
    ERROR HANDLING:
    If user is not associated with an institution, institution variable becomes None
    and template will handle showing appropriate error messages.
    """
    
    # STEP 1: Find the institution associated with the current admin user
    try:
        # Look for institution where the admin field matches the current user
        # This assumes each institution has exactly one admin user
        institution = Institution.objects.get(admin=request.user)
    except Institution.DoesNotExist:
        # Handle case where user is not associated with any institution
        # This shouldn't happen in normal operation, but good to handle edge cases
        institution = None

    # STEP 2: Gather data for dashboard display
    # Get all news items, ordered by most recent first
    # "-created_at" means descending order (newest first)
    news_list = News.objects.order_by("-created_at")
    
    # Get courses, but only for this institution (data isolation)
    # If institution is None, return empty QuerySet instead of all courses
    courses = Course.objects.filter(institution=institution) if institution else Course.objects.none()
    
    # Get teachers, but only for this institution (data isolation) 
    # This prevents admins from seeing teachers from other institutions
    teachers = Teacher.objects.filter(institution=institution) if institution else Teacher.objects.none()

    # STEP 3: Prepare context data for template
    # Context is a dictionary of data that the template can access
    context = {
        'institution': institution,        # Institution data for header/display
        'user': request.user,             # Current user information
        'news_list': news_list,           # All news items for news feed
        'courses': courses,               # Institution's course offerings
        'teachers': teachers,             # Institution's faculty roster
        'show_dashboard_nav': True,       # Flag to show dashboard navigation
    }

    # STEP 4: Render and return the dashboard template
    return render(request, 'institution/dashboard.html', context)


# ================================================================================
# PORTAL ACCESS SYSTEM
# ================================================================================
# The portal system allows institution admins to access teacher and student views
# without needing separate accounts. This is useful for:
# - Testing the system from different user perspectives
# - Helping teachers/students troubleshoot issues
# - Administrative oversight and monitoring

@ensure_csrf_cookie  # Security: ensure CSRF protection
@never_cache  # Security: don't cache portal access pages
@login_required(login_url='login')  # Only authenticated users can access portals
def teacher_portal_login(request):
    """
    WHAT THIS FUNCTION DOES:
    Provides a way for institution admins to access the teacher interface.
    This allows admins to see what teachers see and help troubleshoot issues.
    
    PARAMETERS:
    - request: Django HttpRequest object
    
    RETURN VALUE:
    Either redirects to teacher dashboard or shows portal login form
    
    BUSINESS LOGIC:
    1. Check if current user is already a teacher → redirect to teacher dashboard
    2. If not, show portal login form where admin can enter teacher details
    3. Validate teacher credentials and switch to teacher view
    
    WHO CAN USE THIS:
    Only institution administrators. Regular teachers use the normal login system.
    
    WHY IS THIS USEFUL?
    - Admins can test teacher functionality
    - Admins can help teachers troubleshoot problems
    - Provides administrative oversight capability
    """
    # Import here to avoid circular import issues
    from accounts.models import UserProfile
    
    # STEP 1: Check if current user is already a teacher
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.role == 'teacher':
            # User is already a teacher, send them to teacher dashboard
            return redirect('teacher_dashboard')
    except UserProfile.DoesNotExist:
        # User has no profile, continue with portal login process
        pass
    
    # STEP 2: Use helper function to handle portal login process
    return _handle_portal_login(request, role='teacher')


@ensure_csrf_cookie  # Security: ensure CSRF protection
@never_cache  # Security: don't cache portal access pages  
@login_required(login_url='login')  # Only authenticated users can access portals
def student_portal_login(request):
    """
    WHAT THIS FUNCTION DOES:
    Provides a way for institution admins to access the student interface.
    Similar to teacher portal but for student perspective.
    
    PARAMETERS:
    - request: Django HttpRequest object
    
    RETURN VALUE: 
    Either redirects to student dashboard or shows portal login form
    
    BUSINESS LOGIC:
    Same as teacher portal but for students:
    1. Check if current user is already a student → redirect to student dashboard
    2. If not, show portal login form for student access
    3. Validate student credentials and switch to student view
    
    USE CASES:
    - Admin wants to see what student experience looks like
    - Admin needs to help student with their account
    - Testing student functionality during development
    """
    # Import here to avoid circular import issues
    from accounts.models import UserProfile
    
    # STEP 1: Check if current user is already a student
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.role == 'student':
            # User is already a student, send them to student dashboard
            return redirect('student_dashboard')
    except UserProfile.DoesNotExist:
        # User has no profile, continue with portal login process
        pass
    
    # STEP 2: Use helper function to handle portal login process
    return _handle_portal_login(request, role='student')


def _handle_portal_login(request, role):
    """
    HELPER FUNCTION: Handles the portal login process for both teachers and students
    
    WHAT THIS FUNCTION DOES:
    This is the core logic for allowing admins to "become" teachers or students
    temporarily. It validates admin permissions and handles the role switching.
    
    PARAMETERS:
    - request: Django HttpRequest object
    - role: String indicating target role ('teacher' or 'student')
    
    RETURN VALUE:
    Either renders portal login form or redirects to appropriate dashboard
    
    BUSINESS LOGIC:
    1. Verify current user is an institution admin (only admins can use portals)
    2. Get the institution associated with this admin
    3. Show portal login form (GET request) or process login (POST request)
    4. Validate entered name and ID against database
    5. Switch user session to the target teacher/student account
    
    SECURITY CONSIDERATIONS:
    - Only institution admins can access this functionality
    - Portal access is limited to users within the same institution
    - Validates both name and ID for additional security
    - Maintains audit trail of portal access
    
    WHY IS THIS A SEPARATE FUNCTION?
    Both teacher and student portal login use identical logic, so we follow
    DRY principle (Don't Repeat Yourself) by creating one reusable function.
    """
    # Import here to avoid circular import issues
    from accounts.models import UserProfile

    # STEP 1: Verify user is an institution admin
    try:
        # Get user's profile to check their role
        profile = request.user.userprofile
        if profile.role != 'institution_admin':
            # User is not an admin, deny access to portal functionality
            messages.error(request, 'Only administrators can use the portal login.')
            return redirect('institution_admin_dashboard')
    except UserProfile.DoesNotExist:
        # User has no profile, this is an error condition
        messages.error(request, 'User profile not found.')
        return redirect('institution_admin_dashboard')

    # STEP 2: Get the institution for data isolation
    try:
        # Find institution where current user is the admin
        institution = Institution.objects.get(admin=request.user)
    except Institution.DoesNotExist:
        # Admin is not associated with any institution, this is an error
        messages.error(request, 'Institution context missing.')
        return redirect('institution_admin_dashboard')

    # STEP 3: Handle GET request - show the portal login form
    if request.method == "GET":
        # Prepare context data for the portal login template
        context = {
            'role': role,  # 'teacher' or 'student'
            'title': 'Teacher Login' if role == 'teacher' else 'Student Login',
            'name_label': 'Teacher Name' if role == 'teacher' else 'Student Name', 
            'code_label': 'Employee ID' if role == 'teacher' else 'Student ID',
        }
        return render(request, 'institution/portal_login.html', context)

    name = " ".join((request.POST.get('name') or "").split())
    code = (request.POST.get('code') or "").strip()

    target_user = None

    if role == "teacher":
        teacher = Teacher.objects.filter(employee_id=code, institution=institution).select_related('user').first()
        if not teacher:
            messages.error(request, f'Teacher with Employee ID "{code}" not found.')
            return redirect('teacher_portal_login')
        target_user = teacher.user

    elif role == "student":
        student = Student.objects.filter(student_id=code, institution=institution).select_related('user').first()
        if not student:
            messages.error(request, f'Student with ID "{code}" not found.')
            return redirect('student_portal_login')
        target_user = student.user

    if target_user:
        login(request, target_user)
        messages.success(request, f"Accessing as {role}: {target_user.username}")
        if role == 'teacher':
            return redirect('teacher_dashboard')
        else:
            return redirect('student_dashboard')

    messages.error(request, 'Invalid login request.')
    return redirect('institution_admin_dashboard')


# 🔹 INSTITUTION ADMIN DASHBOARD (ADD + SHOW NEWS + DEPARTMENTS)
@never_cache
@ensure_csrf_cookie
@csrf_protect
@login_required(login_url='login')
def institution_admin_dashboard(request):
    try:
        institution = Institution.objects.get(admin=request.user)
    except Institution.DoesNotExist:
        messages.error(request, "Institution profile not found.")
        return redirect('login')

    edit_news = None
    edit_id = request.GET.get("edit")
    if edit_id:
        edit_news = News.objects.filter(id=edit_id, institution=institution).first()

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "add_news":
            news_text = request.POST.get("news")
            news_id = request.POST.get("news_id")
            if news_text:
                if news_id:
                    news = get_object_or_404(News, id=news_id, institution=institution)
                    news.content = news_text
                    news.save()
                    messages.success(request, "News updated.")
                else:
                    News.objects.create(content=news_text, institution=institution)
                    messages.success(request, "News published.")

        elif action == "add_department":
            dept_name = request.POST.get("dept_name")
            if dept_name:
                Department.objects.create(name=dept_name, institution=institution)
                messages.success(request, f"Department '{dept_name}' created.")

        elif action == "add_branch":
            branch_name = request.POST.get("branch_name")
            dept_id = request.POST.get("dept_id")
            if branch_name and dept_id:
                dept = get_object_or_404(Department, id=dept_id, institution=institution)
                Branch.objects.create(name=branch_name, department=dept, institution=institution)
                messages.success(request, f"Branch '{branch_name}' added.")

        elif action == "delete_department":
            dept_id = request.POST.get("dept_id")
            if dept_id:
                dept = get_object_or_404(Department, id=dept_id, institution=institution)
                dept_name = dept.name
                dept.delete()
                messages.success(request, f"Department '{dept_name}' deleted.")

        elif action == "edit_department":
            dept_id = request.POST.get("dept_id")
            new_name = request.POST.get("dept_name")
            if dept_id and new_name:
                dept = get_object_or_404(Department, id=dept_id, institution=institution)
                dept.name = new_name
                dept.save()
                messages.success(request, "Department updated.")

        elif action == "delete_branch":
            branch_id = request.POST.get("branch_id")
            if branch_id:
                branch = get_object_or_404(Branch, id=branch_id, institution=institution)
                br_name = branch.name
                branch.delete()
                messages.success(request, f"Branch '{br_name}' removed.")

        elif action == "edit_branch":
            branch_id = request.POST.get("branch_id")
            new_name = request.POST.get("branch_name")
            if branch_id and new_name:
                branch = get_object_or_404(Branch, id=branch_id, institution=institution)
                branch.name = new_name
                branch.save()
                messages.success(request, "Branch updated.")

        else:
            # Legacy: plain news form without action field
            news_text = request.POST.get("news")
            news_id = request.POST.get("news_id")
            if news_text:
                if news_id:
                    news = News.objects.get(id=news_id)
                    news.content = news_text
                    news.save()
                else:
                    News.objects.create(content=news_text, institution=institution)

        return redirect("institution_admin_dashboard")

    try:
        news_list = News.objects.filter(institution=institution).order_by("-created_at")
        departments = Department.objects.filter(institution=institution)
    except Exception as e:
        messages.error(request, f"Error loading data: {str(e)}")
        news_list = []
        departments = []

    context = {
        "institution": institution,
        "news_list": news_list,
        "edit_news": edit_news,
        "departments": departments,
        "show_dashboard_nav": True,
        "admin_dashboard_mode": True,
    }
    return render(request, "institution/admin_dashboard.html", context)


@login_required
def delete_news(request, news_id):
    institution = Institution.objects.filter(admin=request.user).first()
    if institution:
        News.objects.filter(id=news_id, institution=institution).delete()
        messages.success(request, "News deleted.")
    return redirect('institution_admin_dashboard')


@login_required
def department_list(request):
    try:
        institution = Institution.objects.get(admin=request.user)
    except Institution.DoesNotExist:
        messages.error(request, "Institution profile not found.")
        return redirect('landing')

    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description", "")
        if name:
            Department.objects.create(institution=institution, name=name, description=description)
            messages.success(request, "Department added successfully.")
        return redirect('department_list')

    departments = Department.objects.filter(institution=institution)
    return render(request, 'institution/department_list.html', {'departments': departments})


@login_required
def delete_department(request, dept_id):
    """Delete a department with proper authorization and cascading"""
    from django.db import transaction
    from generator.models import Timetable
    from academics.models import AttendanceSheet
    
    try:
        institution = Institution.objects.get(admin=request.user)
    except Institution.DoesNotExist:
        messages.error(request, "Not authorized to delete departments.")
        return redirect('institution_admin_dashboard')
    
    # Ensure department belongs to this institution
    department = get_object_or_404(Department, id=dept_id, institution=institution)
    dept_name = department.name
    
    # Gather related data info for logging/confirmation
    related_info = {
        'teachers': department.teacher_set.count(),
        'students': Student.objects.filter(department=department).count(),
        'branches': department.branch_set.count(),
        'timetables': Timetable.objects.filter(department=department).count(),
        'attendance_sheets': AttendanceSheet.objects.filter(department=department).count(),
    }
    
    try:
        with transaction.atomic():
            # The FK relationships handle cascading:
            # - Teacher.department: SET_NULL (teachers remain, dept becomes null)
            # - Student.department: SET_NULL (students remain, dept becomes null)
            # - Branch.department: SET_NULL (branches remain, dept becomes null)
            # - Course.department: SET_NULL (courses remain, dept becomes null)
            # - Timetable.department: CASCADE (timetables deleted)
            # - AttendanceSheet.department: CASCADE (attendance sheets deleted)
            department.delete()
            
        messages.success(
            request, 
            f"Department '{dept_name}' deleted successfully. "
            f"Related data: {related_info['timetables']} timetable(s) and "
            f"{related_info['attendance_sheets']} attendance sheet(s) removed. "
            f"{related_info['teachers']} teacher(s) and {related_info['students']} student(s) unassigned."
        )
    except Exception as e:
        messages.error(request, f"Error deleting department: {str(e)}")
    
    # Check referer to redirect appropriately
    referer = request.META.get('HTTP_REFERER', '')
    if 'department_list' in referer:
        return redirect('department_list')
    return redirect('institution_admin_dashboard')


# ============ ROOM MANAGEMENT ============

@ensure_csrf_cookie
@login_required(login_url='login')
def room_list(request):
    """List all rooms for the institution"""
    try:
        institution = Institution.objects.get(admin=request.user)
    except Institution.DoesNotExist:
        messages.error(request, "Not authorized to view rooms.")
        return redirect('institution_admin_dashboard')
    
    rooms = Room.objects.filter(institution=institution).order_by('number')
    return render(request, 'institution/room_list.html', {
        'rooms': rooms,
        'institution': institution,
    })


@ensure_csrf_cookie
@csrf_protect
@login_required(login_url='login')
def room_create(request):
    """Create a new room"""
    try:
        institution = Institution.objects.get(admin=request.user)
    except Institution.DoesNotExist:
        messages.error(request, "Not authorized to create rooms.")
        return redirect('institution_admin_dashboard')
    
    if request.method == 'POST':
        room_number = request.POST.get('number', '').strip()
        
        if not room_number:
            messages.error(request, "Room number is required.")
            return render(request, 'institution/room_form.html', {
                'action': 'Add',
                'institution': institution,
            })
        
        # Check if room already exists
        if Room.objects.filter(institution=institution, number=room_number).exists():
            messages.error(request, f"Room '{room_number}' already exists.")
            return render(request, 'institution/room_form.html', {
                'action': 'Add',
                'institution': institution,
            })
        
        Room.objects.create(institution=institution, number=room_number)
        messages.success(request, f"Room '{room_number}' created successfully.")
        return redirect('room_list')
    
    return render(request, 'institution/room_form.html', {
        'action': 'Add',
        'institution': institution,
    })


@ensure_csrf_cookie
@csrf_protect
@login_required(login_url='login')
def room_edit(request, room_id):
    """Edit an existing room"""
    try:
        institution = Institution.objects.get(admin=request.user)
    except Institution.DoesNotExist:
        messages.error(request, "Not authorized to edit rooms.")
        return redirect('institution_admin_dashboard')
    
    room = get_object_or_404(Room, id=room_id, institution=institution)
    
    if request.method == 'POST':
        room_number = request.POST.get('number', '').strip()
        
        if not room_number:
            messages.error(request, "Room number is required.")
            return render(request, 'institution/room_form.html', {
                'action': 'Edit',
                'room': room,
                'institution': institution,
            })
        
        # Check if another room has this number
        if Room.objects.filter(institution=institution, number=room_number).exclude(id=room_id).exists():
            messages.error(request, f"Another room with number '{room_number}' already exists.")
            return render(request, 'institution/room_form.html', {
                'action': 'Edit',
                'room': room,
                'institution': institution,
            })
        
        room.number = room_number
        room.save()
        messages.success(request, f"Room updated to '{room_number}'.")
        return redirect('room_list')
    
    return render(request, 'institution/room_form.html', {
        'action': 'Edit',
        'room': room,
        'institution': institution,
    })


@login_required(login_url='login')
def room_delete(request, room_id):
    """Delete a room"""
    try:
        institution = Institution.objects.get(admin=request.user)
    except Institution.DoesNotExist:
        messages.error(request, "Not authorized to delete rooms.")
        return redirect('institution_admin_dashboard')
    
    room = get_object_or_404(Room, id=room_id, institution=institution)
    room_number = room.number
    room.delete()
    messages.success(request, f"Room '{room_number}' deleted successfully.")
    return redirect('room_list')


# ============ ACADEMIC CALENDAR MANAGEMENT ============

@ensure_csrf_cookie
@login_required(login_url='login')
def calendar_list(request):
    """List all academic calendar events for the institution"""
    try:
        institution = Institution.objects.get(admin=request.user)
    except Institution.DoesNotExist:
        messages.error(request, "Not authorized to view calendar.")
        return redirect('institution_admin_dashboard')
    
    events = AcademicCalendarEvent.objects.filter(institution=institution)
    upcoming_events = events.filter(start_date__gte=date.today()).order_by('start_date')
    past_events = events.filter(start_date__lt=date.today()).order_by('-start_date')
    
    return render(request, 'institution/calendar_list.html', {
        'upcoming_events': upcoming_events,
        'past_events': past_events,
        'institution': institution,
        'event_types': AcademicCalendarEvent.EVENT_TYPES,
    })


@ensure_csrf_cookie
@csrf_protect
@login_required(login_url='login')
def calendar_create(request):
    """Create a new calendar event"""
    try:
        institution = Institution.objects.get(admin=request.user)
    except Institution.DoesNotExist:
        messages.error(request, "Not authorized to create events.")
        return redirect('institution_admin_dashboard')
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        event_type = request.POST.get('event_type', 'event')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date') or None
        is_published = request.POST.get('is_published') == 'on'
        
        if not title or not start_date:
            messages.error(request, "Title and start date are required.")
            return render(request, 'institution/calendar_form.html', {
                'action': 'Add',
                'institution': institution,
                'event_types': AcademicCalendarEvent.EVENT_TYPES,
            })
        
        AcademicCalendarEvent.objects.create(
            institution=institution,
            title=title,
            description=description,
            event_type=event_type,
            start_date=start_date,
            end_date=end_date,
            is_published=is_published,
        )
        messages.success(request, f"Event '{title}' created successfully.")
        return redirect('calendar_list')
    
    return render(request, 'institution/calendar_form.html', {
        'action': 'Add',
        'institution': institution,
        'event_types': AcademicCalendarEvent.EVENT_TYPES,
    })


@ensure_csrf_cookie
@csrf_protect
@login_required(login_url='login')
def calendar_edit(request, event_id):
    """Edit an existing calendar event"""
    try:
        institution = Institution.objects.get(admin=request.user)
    except Institution.DoesNotExist:
        messages.error(request, "Not authorized to edit events.")
        return redirect('institution_admin_dashboard')
    
    event = get_object_or_404(AcademicCalendarEvent, id=event_id, institution=institution)
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        event_type = request.POST.get('event_type', 'event')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date') or None
        is_published = request.POST.get('is_published') == 'on'
        
        if not title or not start_date:
            messages.error(request, "Title and start date are required.")
            return render(request, 'institution/calendar_form.html', {
                'action': 'Edit',
                'event': event,
                'institution': institution,
                'event_types': AcademicCalendarEvent.EVENT_TYPES,
            })
        
        event.title = title
        event.description = description
        event.event_type = event_type
        event.start_date = start_date
        event.end_date = end_date
        event.is_published = is_published
        event.save()
        
        messages.success(request, f"Event '{title}' updated successfully.")
        return redirect('calendar_list')
    
    return render(request, 'institution/calendar_form.html', {
        'action': 'Edit',
        'event': event,
        'institution': institution,
        'event_types': AcademicCalendarEvent.EVENT_TYPES,
    })


@login_required(login_url='login')
def calendar_delete(request, event_id):
    """Delete a calendar event"""
    try:
        institution = Institution.objects.get(admin=request.user)
    except Institution.DoesNotExist:
        messages.error(request, "Not authorized to delete events.")
        return redirect('institution_admin_dashboard')
    
    event = get_object_or_404(AcademicCalendarEvent, id=event_id, institution=institution)
    title = event.title
    event.delete()
    messages.success(request, f"Event '{title}' deleted successfully.")
    return redirect('calendar_list')


@login_required(login_url='login')
def calendar_toggle_publish(request, event_id):
    """Toggle publish status of an event"""
    try:
        institution = Institution.objects.get(admin=request.user)
    except Institution.DoesNotExist:
        messages.error(request, "Not authorized.")
        return redirect('institution_admin_dashboard')
    
    event = get_object_or_404(AcademicCalendarEvent, id=event_id, institution=institution)
    event.is_published = not event.is_published
    event.save()
    
    status = "published" if event.is_published else "unpublished"
    messages.success(request, f"Event '{event.title}' {status}.")
    return redirect('calendar_list')
