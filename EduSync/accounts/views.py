# ================================================================================
# ACCOUNTS APP - VIEWS.PY
# ================================================================================
# This file contains all the view functions that handle user authentication,
# login/logout functionality, and user registration processes for the EduSync system.
#
# WHAT ARE VIEWS IN DJANGO?
# Views are Python functions that receive HTTP requests and return HTTP responses.
# They contain the business logic that processes user input and generates output.
#
# WHAT ARE DECORATORS?
# Decorators are functions that modify the behavior of other functions.
# Django provides many useful decorators for views:
# - @never_cache: Prevents browser from caching this page (important for login)
# - @ensure_csrf_cookie: Ensures CSRF token is available for security
# - @csrf_protect: Protects against Cross-Site Request Forgery attacks
# - @require_http_methods: Restricts which HTTP methods (GET, POST) are allowed
# ================================================================================

from django.shortcuts import render, redirect  # Functions to display templates and redirect users
from django.contrib.auth import authenticate, login, logout  # Django's built-in authentication system
from django.contrib.auth.models import User  # Django's default user model for usernames/passwords
from django.views.decorators.http import require_http_methods  # Decorator to restrict HTTP methods
from django.views.decorators.cache import never_cache  # Decorator to prevent caching
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect, csrf_exempt  # CSRF security decorators
from django.contrib import messages  # System to show success/error messages to users

# Import our custom models from the current app and institution app
from .models import UserProfile, LoginTable, SignupTable
from institution.models import Institution


# ==============================
# LANDING PAGE VIEW
# ==============================

@ensure_csrf_cookie  # Ensures CSRF token is available for any forms on this page
@never_cache  # Prevents browser from caching this page (always loads fresh content)
@require_http_methods(["GET"])  # Only allows GET requests (no POST/PUT/DELETE allowed)
def landing_view(request):
    """
    WHAT THIS FUNCTION DOES:
    Displays the main landing/homepage of the EduSync website.
    This is the first page visitors see when they visit the site.
    
    PARAMETERS:
    - request: Django HttpRequest object containing information about the user's request
               (includes user info, cookies, session data, form data, etc.)
    
    RETURN VALUE:
    Returns an HttpResponse object containing the rendered HTML page
    
    BUSINESS LOGIC:
    1. Simply renders the landing.html template
    2. Passes 'force_public_nav' flag to show public navigation instead of user navigation
    
    WHY force_public_nav?
    This tells the template to show the public navigation bar (with Login/Register links)
    instead of the logged-in user navigation bar (with Dashboard/Logout links).
    """
    return render(request, 'landing.html', {'force_public_nav': True})


# ==============================
# UNIFIED LOGIN SYSTEM
# ==============================

@never_cache  # Prevents caching login page (security: always fresh login form)
@ensure_csrf_cookie  # Ensures CSRF token for login form security
@csrf_protect  # Validates CSRF token when form is submitted
@require_http_methods(["GET", "POST"])  # Allows both GET (show form) and POST (submit form)
def unified_login_view(request):
    """
    WHAT THIS FUNCTION DOES:
    Handles the main login system for all user types (Students, Teachers, Admins).
    This is a "unified" login because all user types use the same form but are 
    authenticated differently based on their role and institution.
    
    PARAMETERS:
    - request: Django HttpRequest object containing all request information
    
    RETURN VALUE:
    - GET request: Returns the login form page
    - POST request: Either redirects to appropriate dashboard or shows error messages
    
    BUSINESS LOGIC FLOW:
    1. Check if user is already logged in → redirect to their dashboard
    2. If GET request → show the login form
    3. If POST request → validate credentials and authenticate user
    4. Redirect authenticated user to appropriate dashboard based on their role
    
    AUTHENTICATION PROCESS:
    1. Extract form data (role, institution_name, username, password)
    2. Validate that institution exists in our database
    3. Use Django's authenticate() to verify username/password
    4. Check that user belongs to the specified institution
    5. Check that user's role matches what they selected
    6. Log them in and redirect to appropriate dashboard
    """
    
    # STEP 1: Handle logout parameter - allows users to reach login page even when authenticated
    # This fixes the issue where clicking "Login" redirects to dashboard instead of login form
    logout_param = request.GET.get('logout')
    if logout_param == 'true' and request.user.is_authenticated:
        # User wants to logout first, then see login page
        logout(request)
        messages.info(request, "🔄 You have been logged out. Please login again.")
        return render(request, 'unified_login.html')
    
    # STEP 2: Check if user is already logged in (but allow access to login page with warning)
    # request.user.is_authenticated is a Django property that returns True if user has valid session
    if request.user.is_authenticated:
        # Show a message but still allow access to login page for role switching
        current_role = getattr(request.user.userprofile, 'role', 'unknown') if hasattr(request.user, 'userprofile') else 'unknown'
        messages.warning(request, f"⚠️ You are already logged in as {current_role}. <a href='/logout/' class='alert-link'>Logout first</a> to switch accounts.")
        # Don't auto-redirect - let them see the login form

    # STEP 3: Handle POST request (form submission)
    if request.method == 'POST':
        # Extract form data from the POST request
        # request.POST is like a dictionary containing form field values
        # .get() method safely retrieves values, returning None if key doesn't exist
        # .strip() removes whitespace from beginning and end of strings
        
        role = request.POST.get('role', 'student')  # Default to 'student' if not provided
        institution_name = request.POST.get('institution_name', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        # STEP 4: Validate that all required fields are filled
        # Using 'not' operator checks if strings are empty after stripping whitespace
        if not institution_name or not username or not password:
            # messages.error() adds an error message that will be displayed to user
            messages.error(request, "❌ Please fill in all fields.")
            # Return to login page with error message
            return render(request, 'unified_login.html')

        # STEP 5: Verify that the institution exists in our database
        try:
            # SignupTable stores institution registration information
            # .objects.get() tries to find exactly one matching record
            # institution_name__iexact does case-insensitive exact match
            signup = SignupTable.objects.get(institution_name__iexact=institution_name)
        except SignupTable.DoesNotExist:
            # This exception is raised when no matching institution is found
            messages.error(request, f"❌ Institution '{institution_name}' not found.")
            return render(request, 'unified_login.html')

        # STEP 6: Authenticate the user with Django's built-in system
        # authenticate() checks username and password against Django's User model
        # Returns User object if credentials are valid, None if invalid
        user = authenticate(request, username=username, password=password)

        # STEP 7: Process successful authentication
        if user is not None:
            # User credentials are valid, now check institution and role
            try:
                # Get the user's profile which contains role and institution info
                # UserProfile is connected to User with OneToOneField relationship
                profile = UserProfile.objects.get(user=user)
                
                # STEP 8: Verify institution match
                # Check if user's institution matches what they entered in the form
                # Using .lower() for case-insensitive comparison
                if profile.institution.lower() != institution_name.lower():
                    messages.error(request, f"❌ This account is not registered under {institution_name}.")
                    return render(request, 'unified_login.html')

                # STEP 9: Verify role match
                # Check if user's actual role matches what they selected in the form
                if profile.role != role:
                     messages.error(request, f"❌ Account found, but it is not a {role} account. Please switch tabs.")
                     return render(request, 'unified_login.html')

                # STEP 10: All validations passed - log the user in
                # login() creates a session for the user (sets session cookies)
                login(request, user)
                # Show success message to user
                messages.success(request, f"✅ Welcome back, {user.first_name or user.username}!")
                # Redirect to appropriate dashboard based on user's role
                return _redirect_by_role(user)

            except UserProfile.DoesNotExist:
                # This shouldn't normally happen, but handles edge case where
                # User exists but UserProfile doesn't exist
                messages.error(request, "❌ User profile not found.")
                return render(request, 'unified_login.html')
        else:
            # authenticate() returned None, meaning invalid credentials
            messages.error(request, "❌ Invalid username or password.")
            return render(request, 'unified_login.html')

    # STEP 11: Handle GET request - show the login form
    # If we reach here, it means request.method == 'GET'
    return render(request, 'unified_login.html')


def _redirect_by_role(user):
    """
    HELPER FUNCTION: Redirects user to appropriate dashboard based on their role
    
    WHAT THIS FUNCTION DOES:
    Determines where to send a user after successful login based on their assigned role.
    Different user types (admin, teacher, student) have different dashboard pages.
    
    PARAMETERS:
    - user: Django User object representing the authenticated user
    
    RETURN VALUE:
    Django HttpResponseRedirect object that sends user to appropriate URL
    
    WHY IS THIS A SEPARATE FUNCTION?
    This logic is used in multiple places (login, registration, etc.)
    Following DRY principle (Don't Repeat Yourself) by creating a reusable function.
    
    BUSINESS LOGIC:
    1. Get user's profile to determine their role
    2. Based on role, redirect to appropriate dashboard
    3. Handle edge case where profile doesn't exist
    
    ROLE TYPES:
    - institution_admin: Full admin access to institution management
    - teacher: Access to course and student management  
    - student: Access to personal academic information
    """
    try:
        # Access user's profile through the reverse OneToOne relationship
        # Django automatically creates 'userprofile' attribute on User objects
        profile = user.userprofile
        
        # Check role and redirect accordingly
        if profile.role == 'institution_admin':
            # Redirect to institution admin dashboard
            return redirect('institution_admin_dashboard')
        elif profile.role == 'teacher':
            # Redirect to teacher dashboard
             return redirect('teacher_dashboard')
        elif profile.role == 'student':
            # Redirect to student dashboard
             return redirect('student_dashboard')
    except UserProfile.DoesNotExist:
        # Handle case where user exists but profile doesn't
        # This is an edge case that shouldn't normally happen
        pass
    
    # Default fallback - redirect to landing page if role is unclear
    return redirect('landing')
    
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
    """
    Handles new institution registration and admin account creation.
    Enhanced to allow access even when authenticated, with proper warnings.
    """
    
    # Handle logout parameter - allows users to reach signup page even when authenticated
    logout_param = request.GET.get('logout')
    if logout_param == 'true' and request.user.is_authenticated:
        # User wants to logout first, then see signup page
        logout(request)
        messages.info(request, "🔄 You have been logged out. You can now register a new institution.")
        return render(request, 'signup.html')
    
    # Check if user is already logged in (but allow access to signup page with warning)
    if request.user.is_authenticated:
        # Show a message but still allow access to signup page for new institution registration
        current_role = getattr(request.user.userprofile, 'role', 'unknown') if hasattr(request.user, 'userprofile') else 'unknown'
        current_institution = getattr(request.user.userprofile, 'institution', 'unknown') if hasattr(request.user, 'userprofile') else 'unknown'
        messages.warning(request, f"⚠️ You are already logged in as {current_role} at {current_institution}. <a href='/logout/' class='alert-link'>Logout first</a> to register a new institution.")
        # Don't auto-redirect - let them see the signup form

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
    """
    Logs out the user and redirects to landing page.
    Enhanced to properly clear all session data and prevent authentication persistence.
    Special handling for brand-initiated logouts with stronger security measures.
    """
    if request.user.is_authenticated:
        username = request.user.username
        is_brand_logout = request.POST.get('brand_logout') == 'true'
        
        # Clear the user session completely
        logout(request)
        
        # For brand-initiated logouts, apply extra security measures
        if is_brand_logout:
            # Force session flush and regeneration
            request.session.flush()
            # Clear any cached authentication data
            request.session.cycle_key()
            messages.success(request, f"🚪 {username} has been securely logged out via EduSync brand. Your session is completely cleared.")
        else:
            # Standard logout with session flush
            request.session.flush()
            messages.success(request, f"✅ {username} has been logged out successfully.")
    else:
        messages.info(request, "ℹ️ You were not logged in.")
    
    # Force browser to not cache this response and ensure fresh session
    response = redirect('landing')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response 
