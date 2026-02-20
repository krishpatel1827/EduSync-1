from datetime import date, timedelta
import calendar as py_calendar

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db import IntegrityError
from django.db.models import Q
from .models import Course, Grade, AcademicCalendar, CalendarEvent
from .forms import CourseForm, AcademicCalendarForm, CalendarEventForm
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from institution.models import Institution

from accounts.decorators import role_required
from accounts.utils import get_user_institution


def _get_user_role(user):
    """Get user role from UserProfile"""
    try:
        return user.userprofile.role
    except Exception:
        return None


def _is_admin(user):
    return _get_user_role(user) == 'institution_admin'


def _is_teacher(user):
    return _get_user_role(user) == 'teacher'


def _is_student(user):
    return _get_user_role(user) == 'student'


@ensure_csrf_cookie
@csrf_protect
@login_required(login_url='login')
def course_list(request):
    institution = get_user_institution(request.user)
    if institution:
        courses = Course.objects.filter(institution=institution)
    else:
        courses = Course.objects.all()
    context = {'courses': courses, 'institution': institution, 'is_admin': _is_admin(request.user)}
    return render(request, 'academics/course_list.html', context)


@login_required(login_url='login')
def course_detail(request, course_id):
    institution = get_user_institution(request.user)
    if institution:
        course = get_object_or_404(Course, id=course_id, institution=institution)
    else:
        course = get_object_or_404(Course, id=course_id)
    grades = Grade.objects.filter(course=course)
    context = {'course': course, 'grades': grades, 'is_admin': _is_admin(request.user)}
    return render(request, 'academics/course_detail.html', context)


@ensure_csrf_cookie
@csrf_protect
@login_required(login_url='login')
@role_required('institution_admin')
@never_cache
def course_create(request):
    institution = get_user_institution(request.user)
    if not institution:
        return render(request, 'academics/course_form.html', {
            'form': None,
            'error': 'No institution is associated with this account.'
        })

    if request.method == 'POST':
        form = CourseForm(request.POST, institution=institution)
        if form.is_valid():
            try:
                course = form.save(commit=False)
                course.institution = institution
                course.save()
                form.save_m2m()
                return redirect('course_list')
            except IntegrityError:
                form.add_error('code', 'A course with this code already exists for your institution.')
    else:
        form = CourseForm(institution=institution)

    return render(request, 'academics/course_form.html', {
        'form': form,
        'mode': 'create'
    })


@login_required(login_url='login')
@role_required('institution_admin')
@never_cache
def course_edit(request, course_id):
    institution = get_user_institution(request.user)
    if institution:
        course = get_object_or_404(Course, id=course_id, institution=institution)
    else:
        course = get_object_or_404(Course, id=course_id)

    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course, institution=institution)
        if form.is_valid():
            form.save()
            return redirect('course_list')
    else:
        form = CourseForm(instance=course, institution=institution)

    return render(request, 'academics/course_form.html', {
        'form': form,
        'mode': 'edit',
        'course': course
    })


@login_required(login_url='login')
@role_required('institution_admin')
@require_POST
def course_delete(request, course_id):
    institution = get_user_institution(request.user)
    if institution:
        course = get_object_or_404(Course, id=course_id, institution=institution)
    else:
        course = get_object_or_404(Course, id=course_id)

    course.delete()
    return redirect('course_list')


@login_required(login_url='login')
def academic_calendar_list(request):
    user_institution = get_user_institution(request.user)
    if not user_institution:
        return render(request, 'academics/calendar_list.html', {'calendars': AcademicCalendar.objects.none(), 'is_admin': False})

    # Filter calendars to only show those belonging to the current user's institution
    base_qs = AcademicCalendar.objects.filter(institution=user_institution).select_related('created_by', 'department')
    
    # Also handle the role-based visibility within the institution
    if _is_admin(request.user):
        calendars = base_qs.all()
    elif _is_teacher(request.user):
        teacher_dept = getattr(getattr(request.user, 'teacher', None), 'department', None)
        calendars = base_qs.filter(shared_with_teachers=True)
        if teacher_dept:
            calendars = calendars.filter(Q(department__isnull=True) | Q(department=teacher_dept))
        else:
            calendars = calendars.filter(department__isnull=True)
    elif _is_student(request.user):
        student_dept = getattr(getattr(request.user, 'student', None), 'department', None)
        calendars = base_qs.filter(shared_with_students=True)
        if student_dept:
            calendars = calendars.filter(Q(department__isnull=True) | Q(department=student_dept))
        else:
            calendars = calendars.filter(department__isnull=True)
    else:
        calendars = AcademicCalendar.objects.none()

    # Determine dashboard URL for the back button
    dashboard_url = 'institution_admin_dashboard'
    if _is_teacher(request.user):
        dashboard_url = 'teacher_dashboard'
    elif _is_student(request.user):
        dashboard_url = 'student_dashboard'

    return render(request, 'academics/calendar_list.html', {
        'calendars': calendars, 
        'is_admin': _is_admin(request.user),
        'dashboard_url': dashboard_url
    })


@login_required(login_url='login')
def academic_calendar_detail(request, calendar_id):
    user_institution = get_user_institution(request.user)
    calendar_obj = get_object_or_404(
        AcademicCalendar.objects.filter(institution=user_institution).select_related('created_by', 'department'), 
        id=calendar_id
    )

    # enforce visibility: admins always allowed; teachers/students must have the share flag and match department (if set)
    if not _is_admin(request.user):
        if _is_teacher(request.user):
            if not calendar_obj.shared_with_teachers:
                messages.error(request, 'Calendar is not shared with teachers.')
                return redirect('academic_calendar_list')
            user_dept = getattr(getattr(request.user, 'teacher', None), 'department', None)
        elif _is_student(request.user):
            if not calendar_obj.shared_with_students:
                messages.error(request, 'Calendar is not shared with students.')
                return redirect('academic_calendar_list')
            user_dept = getattr(getattr(request.user, 'student', None), 'department', None)
        else:
            messages.error(request, 'Access denied.')
            return redirect('academic_calendar_list')

        if calendar_obj.department and user_dept != calendar_obj.department:
            messages.error(request, 'This calendar is for a different department.')
            return redirect('academic_calendar_list')

    today = date.today()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))

    month = max(1, min(12, month))

    # compute previous / next months for navigation
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year

    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year

    month_name = py_calendar.month_name[month]
    month_weeks = py_calendar.Calendar(firstweekday=0).monthdayscalendar(year, month)

    events_qs = CalendarEvent.objects.filter(calendar=calendar_obj, date__year=year, date__month=month).order_by('date', 'id')
    events_by_day = {}
    for event in events_qs:
        events_by_day.setdefault(event.date.day, []).append(event)

    context = {
        'calendar_obj': calendar_obj,
        'month': month,
        'year': year,
        'month_name': month_name,
        'month_weeks': month_weeks,
        'events_by_day': events_by_day,
        'events': calendar_obj.events.all().order_by('date', 'id'),
        'is_admin': _is_admin(request.user),
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'type_colors': CalendarEvent.get_type_color_mapping(),
    }
    return render(request, 'academics/calendar_detail.html', context)


@login_required(login_url='login')
@role_required('institution_admin')
def academic_calendar_share(request, calendar_id):
    """Toggle sharing flags for a calendar.

    Accepts POST with `target` in ['students', 'teachers', 'all'].
    - 'students' or 'teachers' toggles the single flag
    - 'all' toggles both flags together (useful for the single "Share" button)
    """
    user_institution = get_user_institution(request.user)
    calendar_obj = get_object_or_404(AcademicCalendar.objects.filter(institution=user_institution), id=calendar_id)
    if request.method == 'POST':
        target = request.POST.get('target')
        if target == 'students':
            calendar_obj.shared_with_students = not calendar_obj.shared_with_students
            calendar_obj.save()
            messages.success(request, f"Shared with students: {calendar_obj.shared_with_students}")
        elif target == 'teachers':
            calendar_obj.shared_with_teachers = not calendar_obj.shared_with_teachers
            calendar_obj.save()
            messages.success(request, f"Shared with teachers: {calendar_obj.shared_with_teachers}")
        elif target == 'all':
            # if either flag is false, set both true; otherwise unset both
            if not (calendar_obj.shared_with_students and calendar_obj.shared_with_teachers):
                calendar_obj.shared_with_students = True
                calendar_obj.shared_with_teachers = True
            else:
                calendar_obj.shared_with_students = False
                calendar_obj.shared_with_teachers = False
            calendar_obj.save()
            messages.success(request, f"Shared with students and teachers: {calendar_obj.shared_with_students and calendar_obj.shared_with_teachers}")
    return redirect('academic_calendar_detail', calendar_id=calendar_obj.id)


@login_required(login_url='login')
@role_required('institution_admin')
def academic_calendar_create(request):
    institution = get_user_institution(request.user)
    if request.method == 'POST':
        form = AcademicCalendarForm(request.POST, institution=institution)
        if form.is_valid():
            calendar_obj = form.save(commit=False)
            calendar_obj.created_by = request.user
            calendar_obj.institution = institution
            calendar_obj.save()
            messages.success(request, 'Academic calendar created successfully.')
            return redirect('academic_calendar_detail', calendar_id=calendar_obj.id)
    else:
        form = AcademicCalendarForm(institution=institution)

    return render(request, 'academics/calendar_form.html', {
        'form': form,
        'mode': 'create',
    })


@login_required(login_url='login')
@role_required('institution_admin')
def academic_calendar_edit(request, calendar_id):
    user_institution = get_user_institution(request.user)
    calendar_obj = get_object_or_404(AcademicCalendar.objects.filter(institution=user_institution), id=calendar_id)
    institution = user_institution

    if request.method == 'POST':
        form = AcademicCalendarForm(request.POST, instance=calendar_obj, institution=institution)
        if form.is_valid():
            form.save()
            messages.success(request, 'Academic calendar updated successfully.')
            return redirect('academic_calendar_detail', calendar_id=calendar_obj.id)
    else:
        form = AcademicCalendarForm(instance=calendar_obj, institution=institution)

    return render(request, 'academics/calendar_form.html', {
        'form': form,
        'mode': 'edit',
        'calendar_obj': calendar_obj,
    })


@login_required(login_url='login')
@role_required('institution_admin')
@require_POST
def academic_calendar_delete(request, calendar_id):
    user_institution = get_user_institution(request.user)
    calendar_obj = get_object_or_404(AcademicCalendar.objects.filter(institution=user_institution), id=calendar_id)
    calendar_obj.delete()
    messages.success(request, 'Academic calendar deleted successfully.')
    return redirect('academic_calendar_list')


@login_required(login_url='login')
@role_required('institution_admin')
def calendar_event_create(request, calendar_id):
    user_institution = get_user_institution(request.user)
    calendar_obj = get_object_or_404(AcademicCalendar.objects.filter(institution=user_institution), id=calendar_id)

    if request.method == 'POST':
        form = CalendarEventForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['date']
            end_date = form.cleaned_data.get('end_date')
            ev_type = form.cleaned_data['type']
            title = ev_type  # simplified: title is derived from the editable type
            color = form.cleaned_data.get('color_code') or CalendarEvent.color_for_type(ev_type)

            # if end_date provided and >= start_date, create events for each date in the inclusive range
            dates = [start_date]
            if end_date and end_date >= start_date:
                cur = start_date
                while cur <= end_date:
                    dates.append(cur)
                    cur = cur + timedelta(days=1)
                # remove the duplicate start_date added earlier
                dates = sorted(set(dates))

            created = 0
            for d in dates:
                # avoid duplicate identical events on same calendar/date/title
                obj, created_flag = CalendarEvent.objects.get_or_create(
                    calendar=calendar_obj, date=d, title=title,
                    defaults={'type': ev_type, 'description': '', 'color_code': color}
                )
                if created_flag:
                    created += 1

            messages.success(request, f'Event added successfully ({created} created).')
            return redirect('academic_calendar_detail', calendar_id=calendar_obj.id)
    else:
        # allow pre-filling the date when creating from a month/day cell
        initial = {}
        pre_date = request.GET.get('date')
        if pre_date:
            initial['date'] = pre_date
        form = CalendarEventForm(initial=initial)

    return render(request, 'academics/event_form.html', {
        'form': form,
        'calendar_obj': calendar_obj,
        'mode': 'create',
        'type_colors': CalendarEvent.get_type_color_mapping(),
    })


@login_required(login_url='login')
@role_required('institution_admin')
def calendar_event_edit(request, event_id):
    user_institution = get_user_institution(request.user)
    event = get_object_or_404(
        CalendarEvent.objects.filter(calendar__institution=user_institution).select_related('calendar'), 
        id=event_id
    )

    if request.method == 'POST':
        form = CalendarEventForm(request.POST, instance=event)
        if form.is_valid():
            ev_type = form.cleaned_data.get('type')
            updated = form.save(commit=False)
            # synchronize title with the editable type (simplified UX)
            if ev_type:
                updated.title = ev_type
            updated.save()
            messages.success(request, 'Event updated successfully.')
            return redirect('academic_calendar_detail', calendar_id=event.calendar_id)
    else:
        form = CalendarEventForm(instance=event)

    return render(request, 'academics/event_form.html', {
        'form': form,
        'calendar_obj': event.calendar,
        'mode': 'edit',
        'event': event,
        'type_colors': CalendarEvent.get_type_color_mapping(),
    })


@login_required(login_url='login')
@role_required('institution_admin')
@require_POST
def calendar_event_delete(request, event_id):
    user_institution = get_user_institution(request.user)
    event = get_object_or_404(CalendarEvent.objects.filter(calendar__institution=user_institution), id=event_id)
    calendar_id = event.calendar_id
    event.delete()
    messages.success(request, 'Event deleted successfully.')
    return redirect('academic_calendar_detail', calendar_id=calendar_id)
