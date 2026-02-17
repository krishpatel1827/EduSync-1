from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from .models import Student
from academics.models import Grade
from institution.models import Institution
from accounts.models import UserProfile
from django.db import transaction, IntegrityError
from .forms import StudentCreateForm, StudentEditForm
from generator.models import Timetable, TimetableEntry


def _unique_username(base):
    username = base
    suffix = 1
    while User.objects.filter(username=username).exists():
        username = f"{base}{suffix}"
        suffix += 1
    return username


def _get_institution_admin(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return None, 'User profile not found.'

    if profile.role != 'institution_admin':
        return None, 'Only institution admins can access this page.'

    try:
        institution = Institution.objects.get(admin=request.user)
    except Institution.DoesNotExist:
        return None, 'No institution is linked to this account.'

    return institution, None


@login_required(login_url='login')
def student_dashboard(request):
    try:
        student = Student.objects.get(user=request.user)
        grades = Grade.objects.filter(student=student)
        
        # Fetch course schedule
        active_tt = Timetable.objects.filter(institution=student.institution, is_active=True).first()
        schedule = []
        if active_tt and student.course:
            entries = TimetableEntry.objects.filter(subject=student.course, timetable=active_tt).select_related('timeslot', 'faculty', 'room', 'division').order_by('timeslot__start_time')
            
            # Group by day
            days_map = {'MON': 'Monday', 'TUE': 'Tuesday', 'WED': 'Wednesday', 'THU': 'Thursday', 'FRI': 'Friday', 'SAT': 'Saturday', 'SUN': 'Sunday'}
            for day_code, day_name in days_map.items():
                day_entries = [e for e in entries if e.day == day_code]
                if day_entries:
                    schedule.append({
                        'day': day_name,
                        'entries': day_entries
                    })

        context = {
            'student': student,
            'grades': grades,
            'schedule': schedule,
        }
        return render(request, 'student/dashboard.html', context)
    except Student.DoesNotExist:
        messages.error(request, 'Student not found.')
        return redirect('dashboard')

@login_required(login_url='login')
def student_grades(request):
    try:
        student = Student.objects.get(user=request.user)
        grades = Grade.objects.filter(student=student).select_related('course')
        context = {'grades': grades, 'student': student}
        return render(request, 'student/grades.html', context)
    except Student.DoesNotExist:
        return render(request, 'student/grades.html', {'error': 'Student profile not found'})


@login_required(login_url='login')
def student_list(request):
    institution, error = _get_institution_admin(request)
    if error:
        return render(request, 'student/student_list.html', {'error': error})

    students = Student.objects.filter(institution=institution).select_related('user', 'course')
    return render(request, 'student/student_list.html', {'students': students})


@login_required(login_url='login')
@never_cache
def student_create(request):
    institution, error = _get_institution_admin(request)
    if error:
        return render(request, 'student/student_form.html', {'error': error})

    if request.method == 'POST':
        form = StudentCreateForm(request.POST, institution=institution)
        if form.is_valid():
            try:
                with transaction.atomic():

                    full_name = form.cleaned_data['name'].strip()
                    parts = full_name.split(None, 1)
                    first_name = parts[0] if parts else full_name
                    last_name = parts[1] if len(parts) > 1 else ""
                    student_id = form.cleaned_data['student_id']
                    username = _unique_username(f"student_{student_id}")
                    password = student_id

                    user = User.objects.create_user(username=username, password=password)
                    user.first_name = first_name
                    user.last_name = last_name
                    user.save()

                    student = Student.objects.create(
                        user=user,
                        institution=institution,
                        student_id=student_id,
                        academic_year=form.cleaned_data.get('academic_year', ''),
                        gender=form.cleaned_data['gender'],
                        date_of_birth=form.cleaned_data.get('date_of_birth'),
                        address=form.cleaned_data.get('address', ''),
                        parent_name=form.cleaned_data.get('parent_name', ''),
                        parent_phone=form.cleaned_data.get('parent_phone', ''),
                        blood_group=form.cleaned_data.get('blood_group', ''),
                        course=form.cleaned_data.get('course'),
                        department=form.cleaned_data.get('department'),
                    )

                    UserProfile.objects.create(
                        user=student.user,
                        role='student',
                        institution=institution.name
                    )
                messages.success(request, 'Student added successfully.')
                return redirect('student_list')
            except IntegrityError as e:
                messages.error(request, f'Database error: One of the unique fields (like Roll No) might already exist. ({e})')
            except Exception as e:
                messages.error(request, f'An unexpected error occurred: {e}')
    else:
        form = StudentCreateForm(institution=institution)

    return render(request, 'student/student_form.html', {'form': form, 'mode': 'create'})


@login_required(login_url='login')
@never_cache
def student_edit(request, student_id):
    institution, error = _get_institution_admin(request)
    if error:
        return render(request, 'student/student_form.html', {'error': error})

    student = get_object_or_404(Student, id=student_id, institution=institution)

    if request.method == 'POST':
        form = StudentEditForm(request.POST, student=student, institution=institution)
        if form.is_valid():
            full_name = form.cleaned_data['name'].strip()
            parts = full_name.split(None, 1)
            student.user.first_name = parts[0] if parts else full_name
            student.user.last_name = parts[1] if len(parts) > 1 else ''
            student.user.save()

            student.student_id = form.cleaned_data['student_id']
            student.academic_year = form.cleaned_data.get('academic_year', '')
            student.gender = form.cleaned_data['gender']
            student.date_of_birth = form.cleaned_data.get('date_of_birth')
            student.address = form.cleaned_data.get('address', '')
            student.parent_name = form.cleaned_data.get('parent_name', '')
            student.parent_phone = form.cleaned_data.get('parent_phone', '')
            student.blood_group = form.cleaned_data.get('blood_group', '')
            student.course = form.cleaned_data.get('course')
            student.department = form.cleaned_data.get('department')
            student.save()

            messages.success(request, 'Student updated successfully.')
            return redirect('student_list')
    else:
        form = StudentEditForm(student=student, institution=institution)

    return render(request, 'student/student_form.html', {
        'form': form,
        'mode': 'edit',
        'student': student
    })


@login_required(login_url='login')
def student_delete(request, student_id):
    institution, error = _get_institution_admin(request)
    if error:
        return render(request, 'student/student_list.html', {'error': error})

    student = get_object_or_404(Student, id=student_id, institution=institution)
    user = student.user
    student.delete()
    user.delete()
    messages.success(request, 'Student deleted successfully.')
    return redirect('student_list')

@login_required
def student_timetable(request):
    try:
        student = Student.objects.get(user=request.user)
        institution = student.institution
        
        # Determine current active timetable for this institution
        # Assuming entries are linked by course (subject) which connects to the student's enrolled course
        
        timetable = Timetable.objects.filter(institution=institution, is_active=True).first()
        
        if not timetable:
             return render(request, 'student/my_timetable.html', {'error': 'No active timetable found.'})
             
        # We need to filter entries relevant to this student.
        # Ideally, a student belongs to a specific Division or Course (Branch).
        # The prompt says "subject of particular branch and student of same branch".
        # In our models, Student has 'course' (ForeignKey to Course).
        # TimetableEntry has 'subject' (ForeignKey to Course).
        # So we filter entries where entry.subject == student.course?
        # WAIT: TimetableEntry also has 'division'.
        # Usually students are in a Division. Our Student model doesn't seem to have 'Division' field explicitly shown above?
        # Let's check Student model.
        
        # Re-reading prompt: "particular branch and a student is of same branch"
        # So we filter entries by student.course.
        
        relevant_entries = TimetableEntry.objects.filter(
            timetable=timetable,
            subject=student.course 
        ).select_related('timeslot', 'faculty', 'room', 'division', 'subject').order_by('day', 'timeslot__lecture_number')
        
        # But wait, a timetable usually has ALL subjects for a division.
        # If the student is in "B.Tech CS", their timetable should show ALL classes for "B.Tech CS".
        # If 'student.course' represents the Branch (e.g. B.Tech CS), then yes.
        # But usually 'TimetableEntry.subject' is a specific subject like "Data Structures".
        # And "Data Structures" belongs to "B.Tech CS".
        # Let's check models to be sure.
        
        # Assumption: Student.course is the "Program/Branch" (e.g. B.Tech CS).
        # AND TimetableEntry.subject is ALSO the "Program/Branch"? 
        # OR TimetableEntry.subject is a specific subject?
        
        # Let's look at `create_demo_data.py` or similar to see what Course means.
        # Course name="B.Tech Computer Science".
        # So yes, Student.course is the big program.
        # TimetableEntry.subject is... wait.
        # In generator/views.py: subjects = Course.objects.filter(...)
        # So 'subject' in TimetableEntry IS the Course model.
        # If the Course model represents "B.Tech CS", then assigning "B.Tech CS" to a slot means "Class for B.Tech CS".
        
        # So yes, filter entries where subject=student.course.
        
        # Construct grid data similar to timetable_view but only for this student's course
        
        divisions = list(set(e.division for e in relevant_entries))
        # If there are multiple divisions for the same course (e.g. D1, D2), the student should ideally know their division.
        # Since Student model logic for division isn't clear, we might show all or just the first?
        # Prompt says "student can see the time table of his".
        # Let's show all divisions for that course if multiple exist, or just the grid.
        
        # Actually, let's just reuse the timetable structure but filtered.
        
        days = [
            ('MON', 'Monday'), ('TUE', 'Tuesday'), ('WED', 'Wednesday'),
            ('THU', 'Thursday'), ('FRI', 'Friday'), ('SAT', 'Saturday'), ('SUN', 'Sunday')
        ][:timetable.days_count]
        
        timeslots = list(set(e.timeslot for e in relevant_entries))
        timeslots.sort(key=lambda x: x.lecture_number)
        
        # We need all timeslots from the timetable to show gaps/breaks correctly
        all_timeslots = timetable.timeslots.all().order_by('lecture_number')
        
        timetable_data = []
        for day_code, day_name in days:
            day_slots = []
            for slot in all_timeslots:
                # Find entry for this student's course at this slot
                # (Ignoring division for a moment, or assuming they want to see "B.Tech CS" classes)
                entry = TimetableEntry.objects.filter(
                    timetable=timetable,
                    day=day_code,
                    timeslot=slot,
                    subject=student.course
                ).first()
                
                day_slots.append({
                    'slot': slot,
                    'entry': entry
                })
            timetable_data.append({
                'day_code': day_code,
                'day_name': day_name,
                'slots': day_slots
            })

        context = {
            'student': student,
            'current_timetable': timetable,
            'timetable_data': timetable_data,
            'semester_text': timetable.footer_semester_text, # Using the dynamic field
        }
        return render(request, 'student/my_timetable.html', context)
        
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('dashboard')
