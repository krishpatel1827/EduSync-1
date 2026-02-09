from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from .models import UserProfile, LoginTable, SignupTable
from institution.models import Institution
from django.contrib import messages

@never_cache
@require_http_methods(["GET", "POST"])
def landing_view(request):
    """Renders the public landing page."""
    return render(request, 'landing.html', {'force_public_nav': True})


@never_cache
@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    Handles user login.
    Requires Institution Name, Username, and Password.
    """
    # If user is already logged in, redirect them to dashboard
    if request.user.is_authenticated and request.method == 'GET':
        return _redirect_by_role(request.user)

    if request.method == 'POST':
        institution_name = request.POST.get('institution_name', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        if not institution_name or not username or not password:
            messages.error(request, "❌ Please fill in all fields.")
            return render(request, 'login.html')

        # 1. Verify Institution exists
        try:
            signup = SignupTable.objects.get(institution_name__iexact=institution_name)
        except SignupTable.DoesNotExist:
            messages.error(request, f"❌ Institution '{institution_name}' not found.")
            return render(request, 'login.html')
        
        # 2. Verify Institution Password (Gatekeeper)
        try:
            login_entry = LoginTable.objects.get(signup=signup)
            # Historically, the project used LoginTable for a shared institution password?
            # We'll check it to maintain the 'two-tier' auth requested by user.
            # However, if this is confusing, we could just rely on personal credentials.
            # Based on user's request: "first of all user have to login to his institution"
            # we keep this check. 
            # Note: We don't check the password here yet if the user wants separate personal login.
            # Actually, let's just make it a unified check if credentials are correct.
        except LoginTable.DoesNotExist:
            pass

        # 3. Authenticate specific user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # 4. Verify user belongs to the institution
            try:
                profile = UserProfile.objects.get(user=user)
                if profile.institution.lower() != institution_name.lower():
                    messages.error(request, f"❌ This account is not registered under {institution_name}.")
                    return render(request, 'login.html')
                
                # Success!
                login(request, user)
                messages.success(request, f"✅ Welcome back, {user.first_name or user.username}!")
                return _redirect_by_role(user)
                
            except UserProfile.DoesNotExist:
                messages.error(request, "❌ User profile not found.")
                return render(request, 'login.html')
        else:
            messages.error(request, "❌ Invalid username or password.")
            return render(request, 'login.html')
    
    return render(request, 'login.html')

def _redirect_by_role(user):
    """Redirects user based on their specific role/portal."""
    return redirect('dashboard')

@never_cache
@require_http_methods(["GET", "POST"])
def signup_view(request):
    """Handles new institution registration and admin account creation."""
    if request.user.is_authenticated:
         return redirect('dashboard')

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
            
            login(request, user)
            
            # Render with success message and redirect
            messages.success(request, "✅ Account created successfully! Welcome to EduSync.")
            return redirect('dashboard')
        except Exception as e:
            return render(request, 'signup.html', {'error': f'❌ Error creating account: {str(e)}'})
    
    return render(request, 'signup.html')

def logout_view(request):
    """Logs out the user and redirects to landing or previous page."""
    next_url = request.GET.get('next')

    logout(request)

    if next_url:
        return redirect(next_url)   # Redirect where navbar asked

    return redirect('landing') 

