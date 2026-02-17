from django.shortcuts import render, redirect

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

from .models import Institution, News, Department
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





# 🔹 INSTITUTION ADMIN DASHBOARD (ADD + SHOW NEWS)
@never_cache
@login_required(login_url='login')
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
    Department.objects.filter(id=dept_id).delete()
    messages.success(request, "Department deleted.")
    return redirect('department_list')
