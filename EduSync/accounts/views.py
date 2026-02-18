from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect, csrf_exempt
from django.contrib import messages

from .models import UserProfile, LoginTable, SignupTable
from institution.models import Institution


# ==============================
# LANDING
# ==============================

@ensure_csrf_cookie
@never_cache
@require_http_methods(["GET"])
def landing_view(request):
    """Renders the public landing page."""
    return render(request, 'landing.html', {'force_public_nav': True})


# ==============================
# UNIFIED LOGIN
# ==============================

@never_cache
@ensure_csrf_cookie
@csrf_protect
@require_http_methods(["GET", "POST"])
def unified_login_view(request):
    """
    Handles unified login for Students, Teachers, and Admins.
    """
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    if request.method == 'POST':
        role = request.POST.get('role', 'student') 
        institution_name = request.POST.get('institution_name', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not institution_name or not username or not password:
            messages.error(request, "❌ Please fill in all fields.")
            return render(request, 'unified_login.html')

        # 1. Verify Institution exists
        try:
            signup = SignupTable.objects.get(institution_name__iexact=institution_name)
        except SignupTable.DoesNotExist:
            messages.error(request, f"❌ Institution '{institution_name}' not found.")
            return render(request, 'unified_login.html')

        # 2. Authenticate User
        user = authenticate(request, username=username, password=password)

        if user is not None:
            try:
                profile = UserProfile.objects.get(user=user)
                
                # 3. Verify Institution Match
                if profile.institution.lower() != institution_name.lower():
                    messages.error(request, f"❌ This account is not registered under {institution_name}.")
                    return render(request, 'unified_login.html')

                # 4. Verify Role Match
                if profile.role != role:
                     messages.error(request, f"❌ Account found, but it is not a {role} account. Please switch tabs.")
                     return render(request, 'unified_login.html')

                # Success
                login(request, user)
                messages.success(request, f"✅ Welcome back, {user.first_name or user.username}!")
                return _redirect_by_role(user)

            except UserProfile.DoesNotExist:
                messages.error(request, "❌ User profile not found.")
                return render(request, 'unified_login.html')
        else:
            messages.error(request, "❌ Invalid username or password.")
            return render(request, 'unified_login.html')

    return render(request, 'unified_login.html')

def _redirect_by_role(user):
    """Redirects user based on their specific role."""
    try:
        profile = user.userprofile
        if profile.role == 'institution_admin':
            return redirect('institution_admin_dashboard')
        elif profile.role == 'teacher':
             return redirect('teacher_dashboard')
        elif profile.role == 'student':
             return redirect('student_dashboard')
    except UserProfile.DoesNotExist:
        pass
    
    # Fallback - redirect to landing page instead of generator
    return redirect('landing')


# ==============================
# SIGNUP
# ==============================

@never_cache
@ensure_csrf_cookie
@csrf_protect
@require_http_methods(["GET", "POST"])
def signup_view(request):
    """Handles new institution registration and admin account creation."""
    if request.user.is_authenticated:
         return _redirect_by_role(request.user)

    if request.method == 'POST':

        institution_name = request.POST.get('institution')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Check if institution name already exists
        if Institution.objects.filter(name=institution_name).exists():
            return render(request, 'signup.html', {'error': 'Institution already exists'})
        
        if SignupTable.objects.filter(institution_name=institution_name).exists():
            return render(request, 'signup.html', {'error': 'Institution name already registered'})
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            return render(request, 'signup.html', {'error': '❌ Username already exists. Please choose a different username.'})
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            return render(request, 'signup.html', {'error': '❌ Email already registered. Please use a different email.'})
        
        try:
            # Create SignupTable entry (institution details)
            signup = SignupTable.objects.create(
                institution_name=institution_name,
                email=email
            )
            
            # Create LoginTable entry (login credentials)
            LoginTable.objects.create(
                signup=signup,
                institution_name=institution_name,
                password=password
            )
            
            # Create user
            user = User.objects.create_user(username=username, email=email, password=password)
            
            # Create UserProfile as institution admin
            UserProfile.objects.create(user=user, role='institution_admin', institution=institution_name)
            
            # Create Institution
            Institution.objects.create(name=institution_name, admin=user, email=email)
            
            # Don't auto-login, redirect to login page with success message
            messages.success(request, "✅ Account created successfully! Please log in to access your dashboard.")
            return redirect('login')
        except Exception as e:
            return render(request, 'signup.html', {'error': f'❌ Error creating account: {str(e)}'})
    
    return render(request, 'signup.html')


# ==============================
# LOGOUT
# ==============================

@never_cache
@require_http_methods(["GET", "POST"])
def logout_view(request):
    """Logs out the user and redirects to landing page."""
    logout(request)
    messages.success(request, "✅ You have been logged out successfully.")
    return redirect('landing') 
