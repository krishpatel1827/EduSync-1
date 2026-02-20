from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def _get_user_role(user):
    """Get user role from UserProfile"""
    try:
        return user.userprofile.role
    except Exception:
        return None


def admin_required(view_func):
    """Decorator to require admin role"""
    @wraps(view_func)
    @login_required(login_url='login')
    def wrapper(request, *args, **kwargs):
        if _get_user_role(request.user) != 'institution_admin':
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def teacher_required(view_func):
    """Decorator to require teacher role"""
    @wraps(view_func)
    @login_required(login_url='login')
    def wrapper(request, *args, **kwargs):
        if _get_user_role(request.user) != 'teacher':
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def student_required(view_func):
    """Decorator to require student role"""
    @wraps(view_func)
    @login_required(login_url='login')
    def wrapper(request, *args, **kwargs):
        if _get_user_role(request.user) != 'student':
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(*roles):
    """Decorator to require specific roles"""
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url='login')
        def wrapper(request, *args, **kwargs):
            if _get_user_role(request.user) not in roles:
                role = _get_user_role(request.user)
                messages.error(request, 'You are not authorized to do that if button is accessed from student and teacher dashbord only admin has rights to change it')
                if role == 'teacher':
                    return redirect('teacher_dashboard')
                elif role == 'student':
                    return redirect('student_dashboard')
                return redirect('login')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
