from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

from .models import Institution, News
from academics.models import Course
from teacher.models import Teacher
from student.models import Student


# 🔹 INSTITUTION DASHBOARD (WELCOME PAGE)
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
        'teachers': teachers,          # ✅ NEWS PASSED HERE
        'show_dashboard_nav': True,
    }

    return render(request, 'institution/dashboard.html', context)


@never_cache
@login_required(login_url='login')
def teacher_portal_login(request):
    # Check if we are already a teacher
    if hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'teacher':
        return redirect('generator') 
        
    return _handle_portal_login(request, role='teacher')


@never_cache
@login_required(login_url='login')
def student_portal_login(request):
    # Check if we are already a student
    if hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'student':
        return redirect('student_dashboard')

    return _handle_portal_login(request, role='student')


def _handle_portal_login(request, role):
    # Get the current institution from the logged-in admin
    try:
        # If currently an admin
        if request.user.userprofile.role == 'institution_admin':
            institution = Institution.objects.get(admin=request.user)
        else:
            # If accidentally here as another role, try to find institution from profile
            institution_name = request.user.userprofile.institution
            institution = Institution.objects.get(name=institution_name)
            
    except (Institution.DoesNotExist, AttributeError):
        messages.error(request, 'Institution context missing. Please log in as Institution Admin first.')
        return redirect('dashboard')

    if request.method == "GET":
        context = {
            'role': role,
            'title': 'Teacher Login' if role == 'teacher' else 'Student Login',
            'name_label': 'Teacher Name' if role == 'teacher' else 'Student Name',
            'code_label': 'Employee ID' if role == 'teacher' else 'Roll No.',
            'name_placeholder': 'Enter teacher name' if role == 'teacher' else 'Enter student name',
            'code_placeholder': 'Enter employee ID' if role == 'teacher' else 'Enter roll number',
        }
        return render(request, 'institution/portal_login.html', context)

    name = " ".join((request.POST.get('name') or "").split())
    code = (request.POST.get('code') or "").strip()

    def normalize(value):
        return " ".join((value or "").split()).lower()

    target_user = None

    if role == "teacher":
        teacher = Teacher.objects.filter(employee_id=code, institution=institution).select_related('user').first()
        if not teacher:
            messages.error(request, f'Teacher with Employee ID "{code}" not found.')
            return redirect('teacher_portal_login')

        full_name = teacher.user.get_full_name()
        user_name = teacher.user.username
        
        expected_names = {normalize(full_name), normalize(user_name)}
        if normalize(name) not in expected_names:
            messages.error(request, f'Name mismatch. Expected "{full_name}" or "{user_name}".')
            return redirect('teacher_portal_login')
            
        target_user = teacher.user

    elif role == "student":
        student = Student.objects.filter(student_id=code, institution=institution).select_related('user').first()
        if not student:
            messages.error(request, f'Student with Roll No "{code}" not found.')
            return redirect('student_portal_login')

        full_name = student.user.get_full_name()
        user_name = student.user.username
        
        expected_names = {normalize(full_name), normalize(user_name)}
        if normalize(name) not in expected_names:
            messages.error(request, f'Name mismatch. Expected "{full_name}" or "{user_name}".')
            return redirect('student_portal_login')
            
        target_user = student.user

    if target_user:
        # 🚀 MAGIC SWAP: Log in as the target user without password
        # We trust the Institution Admin who is currently logged in
        login(request, target_user)
        
        messages.success(request, f"Accessing as {role}: {target_user.get_full_name()}")
        
        if role == 'teacher':
             return redirect('generator')
        else:
             return redirect('student_dashboard')

    messages.error(request, 'Invalid login request.')
    return redirect('dashboard')


@never_cache
def institution_admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        print(f"DEBUG: Login attempt - Username: {username}, Password: {password}")
        print()
        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(request, 'institution/admin_login.html', {'error': "❌ Username or password is wrong"})

        if not hasattr(user, 'userprofile') or user.userprofile.role != 'institution_admin':
            return render(request, 'institution/admin_login.html', {'error': "❌ You are not an institution admin"})

        login(request, user)
        messages.success(request, "✅ Login successful, welcome to the admin dashboard!")
        return redirect('institution_admin_dashboard')

    return render(
        request,
        'institution/admin_login.html'
    )


# 🔹 INSTITUTION ADMIN DASHBOARD (ADD + SHOW NEWS)
@never_cache
@login_required(login_url='institution_admin_login')
def institution_admin_dashboard(request):
    edit_news = None

    # EDIT MODE
    edit_id = request.GET.get("edit")
    if edit_id:
        edit_news = News.objects.filter(id=edit_id).first()

    # CREATE / UPDATE
    if request.method == "POST":
        news_text = request.POST.get("news")
        news_id = request.POST.get("news_id")

        if news_text:
            if news_id:
                # UPDATE
                news = News.objects.get(id=news_id)
                news.content = news_text
                news.save()
            else:
                # CREATE
                News.objects.create(content=news_text)

        return redirect("institution_admin_dashboard")

    news_list = News.objects.order_by("-created_at")

    return render(
        request,
        "institution/admin_dashboard.html",
        {
            "news_list": news_list,
            "edit_news": edit_news,
            "show_dashboard_nav": True,
            "admin_dashboard_mode": True
            
        }
    )

@login_required
def delete_news(request, news_id):
    News.objects.filter(id=news_id).delete()
    return redirect('institution_admin_dashboard')
