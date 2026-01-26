from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login

def landing(request):
    return render(request, 'landing.html')

def signup(request):
    if request.method == 'POST':
        institution = request.POST['institution']
        email = request.POST['email']
        password = request.POST['password']

        user = User.objects.create_user(
            username=institution,
            email=email,
            password=password
        )
        user.save()
        return redirect('login')

    return render(request, 'signup.html')

def login_view(request):
    if request.method == 'POST':
        user = authenticate(
            username=request.POST['username'],
            password=request.POST['password']
        )
        if user:
            login(request, user)
            return redirect('institution_dashboard')

    return render(request, 'login.html')
