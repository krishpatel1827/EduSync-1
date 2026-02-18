from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect

from .models import Institution, News, Department
from academics.models import Course, Branch
from teacher.models import Teacher
from student.models import Student
from generator.models import Room


# 🔹 INSTITUTION DASHBOARD (WELCOME PAGE)
@ensure_csrf_cookie
@csrf_protect
@never_cache
@login_required(login_url='login')
def dashboard_view(request):
    try:
        institution = Institution.objects.get(admin=request.user)
    except Institution.DoesNotExist:
        institution = None

    news_list = News.objects.order_by("-created_at")
    courses = Course.objects.filter(institution=institution) if institution else Course.objects.none()
    teachers = Teacher.objects.filter(institution=institution) if institution else Teacher.objects.none()

    context = {
        'institution': institution,
        'user': request.user,
        'news_list': news_list,
        'courses': courses,
        'teachers': teachers,
        'show_dashboard_nav': True,
    }

    return render(request, 'institution/dashboard.html', context)


# 🔹 PORTAL LOGIN — Admin role-switching
@ensure_csrf_cookie
@never_cache
@login_required(login_url='login')
def teacher_portal_login(request):
    """Shortcut for Admin to log in as a Teacher"""
    from accounts.models import UserProfile
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.role == 'teacher':
            return redirect('teacher_dashboard')
    except UserProfile.DoesNotExist:
        pass
    return _handle_portal_login(request, role='teacher')


@ensure_csrf_cookie
@never_cache
@login_required(login_url='login')
def student_portal_login(request):
    """Shortcut for Admin to log in as a Student"""
    from accounts.models import UserProfile
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.role == 'student':
            return redirect('student_dashboard')
    except UserProfile.DoesNotExist:
        pass
    return _handle_portal_login(request, role='student')


def _handle_portal_login(request, role):
    """Helper to handle portal logic for swapping roles within an institution"""
    from accounts.models import UserProfile

    # Check if user is admin
    try:
        profile = request.user.userprofile
        if profile.role != 'institution_admin':
            messages.error(request, 'Only administrators can use the portal login.')
            return redirect('institution_admin_dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('institution_admin_dashboard')

    try:
        institution = Institution.objects.get(admin=request.user)
    except Institution.DoesNotExist:
        messages.error(request, 'Institution context missing.')
        return redirect('institution_admin_dashboard')

    if request.method == "GET":
        context = {
            'role': role,
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
        return redirect('dashboard')

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
