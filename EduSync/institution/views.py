from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Institution

@login_required(login_url='login')
def dashboard_view(request):
    try:
        institution = Institution.objects.get(admin=request.user)
    except Institution.DoesNotExist:
        institution = None

    context = {
        'institution': institution,
        'user': request.user,
        'show_dashboard_nav': True,  # DASHBOARD NAVBAR
    }
    return render(request, 'institution/dashboard.html', context)


def institution_admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, "❌ Username or password is wrong")
            return redirect('institution_admin_login')

        # role check
        if user.userprofile.role != 'institution_admin':
            messages.error(request, "❌ You are not an institution admin")
            return redirect('institution_admin_login')

        login(request, user)

        return redirect('institution_admin_dashboard')

    context = {
        'show_dashboard_nav': True  # Show dashboard navbar even on login page
    }

    return render(request, 'institution/admin_login.html', context)


@login_required(login_url='institution_admin_login')
def institution_admin_dashboard(request):
    context = {
        'show_dashboard_nav': True
    }
    return render(request, 'institution/admin_dashboard.html', context)
