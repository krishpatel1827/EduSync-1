from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.urls import reverse
from django.http import Http404, JsonResponse
from django.db import models
from django.contrib.auth.models import User
import json

# Correct imports for existing models
from institution.models import Department, Institution
from academics.models import Course as Subject # Using existing Course model alias
from student.models import Student  # Use existing Student model
from accounts.models import UserProfile
from accounts.utils import get_user_institution
from .models import TeacherSubject, Marksheet, Marks

# ===================================
# 1. Admin View: Dynamic Marksheet Table
# ===================================
@login_required
def admin_marksheet_view(request):
    # Check if user is institution admin using EduSync's role system
    try:
        profile = request.user.userprofile
        if profile.role != 'institution_admin':
            messages.error(request, "Access denied. Admin privileges required.")
            return redirect('landing')
            
        # Get admin's institution
        try:
            institution = Institution.objects.get(admin=request.user)
        except Institution.DoesNotExist:
            messages.error(request, "Institution not found for your account.")
            return redirect('landing')
            
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found.")
        return redirect('landing')

    # Get departments for this institution only
    departments = Department.objects.filter(institution=institution)
    selected_dept_id = request.GET.get('department')
    selected_sem = request.GET.get('semester')
    
    context = {'departments': departments, 'institution': institution, 'selected_dept_id': selected_dept_id, 'selected_sem': selected_sem}
    
    if selected_dept_id and selected_sem:
        try:
            dept = get_object_or_404(Department, id=selected_dept_id, institution=institution)
            
            # 1. Get Subjects (Using existing Course model, filtered by department)
            subjects = Subject.objects.filter(department=dept).order_by('code')
            
            # 2. Get Students (Rows) - using existing Student model  
            students = Student.objects.filter(department=dept, institution=institution).select_related('user')
            
            # 3. Build Matrix
            matrix_data = []
            for student in students:
                # Fetch marksheet for this semester
                marksheet = Marksheet.objects.filter(
                    student=student.user, 
                    semester=selected_sem
                ).first()
                
                # Map Subject ID -> Marks Object
                marks_map = {}
                if marksheet:
                    user_marks = Marks.objects.filter(marksheet=marksheet)
                    for m in user_marks:
                        marks_map[m.subject_id] = m
                
                # Create Row: Student + List of Marks/Empty cells
                row_marks = []
                for subj in subjects:
                    # Get mark object if exists, else None
                    row_marks.append(marks_map.get(subj.id))
                
                matrix_data.append({
                    'student': student,
                    'row_marks': row_marks, 
                    'total': marksheet.total_marks if marksheet else '-',
                    'grade': marksheet.final_grade if marksheet else '-'
                })
                
            context.update({
                'selected_dept': dept,
                'selected_sem': selected_sem,
                'subjects': subjects,
                'matrix_data': matrix_data
            })
        
        except Department.DoesNotExist:
            messages.error(request, f"Department not found or not accessible.")
        except Exception as e:
            messages.error(request, f"Error loading data: {str(e)}")
    
    return render(request, 'marksheet/admin_dashboard.html', context)


# ===================================
# 2. Teacher View: Marks Entry
# ===================================
@login_required
def teacher_marks_entry(request):
    """
    Teacher marks entry interface
    """
    # Check if user is teacher or admin
    try:
        profile = request.user.userprofile
        if profile.role not in ['teacher', 'institution_admin']:
            messages.error(request, "Access denied. Teacher privileges required.")
            return redirect('landing')
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found.")
        return redirect('landing')
    # 1. Get subjects assigned to this teacher
    try:
        assigned_subjects = TeacherSubject.objects.filter(teacher=request.user).select_related('subject')
        subjects = [ts.subject for ts in assigned_subjects] # List of Course objects
    except Exception as e:
        messages.error(request, f"Error loading subjects: {str(e)}")
        subjects = []
    
    context = {'subjects': subjects}
    
    selected_subject_id = request.GET.get('subject')
    selected_semester = request.GET.get('semester') # Added semester selector since Course lacks it
    
    if selected_subject_id:
        try:
            subject = Subject.objects.get(id=selected_subject_id)
            
            if not assigned_subjects.filter(subject=subject).exists():
                messages.error(request, "Access Denied.")
                return redirect('teacher_marks_entry')
                
            department = subject.department
            context['selected_subject'] = subject

            # Only proceed if semester is selected
            if selected_semester:
                semester = int(selected_semester)
                students = Student.objects.filter(department=department).select_related('user')
                context['selected_semester'] = semester

                # 3. Process Form Submission
                if request.method == 'POST':
                    with transaction.atomic():
                        for student in students:
                            marks_val = request.POST.get(f'marks_{student.user.id}')
                            
                            if marks_val and marks_val.strip():
                                try:
                                    marks_int = int(marks_val)
                                    if marks_int < 0 or marks_int > 100: # Assuming 100 max
                                        continue

                                    marksheet, _ = Marksheet.objects.get_or_create(
                                        student=student.user,
                                        semester=semester,
                                        defaults={'academic_year': '2025-2026'} 
                                    )
                                    
                                    marks_obj, created = Marks.objects.get_or_create(
                                        marksheet=marksheet,
                                        subject=subject,
                                        defaults={'marks': 0}
                                    )
                                    
                                    marks_obj.marks = marks_int
                                    marks_obj.save() 
                                    
                                except ValueError:
                                    pass
                    
                    messages.success(request, f"Marks updated for {subject.name}")
                    # Redirect back with current parameters
                    redirect_url = f"{reverse('teacher_enter_marks')}?subject={selected_subject_id}&semester={selected_semester}"
                    return redirect(redirect_url)

                # 4. Prepare Data for View
                student_list = []
                for student in students:
                    current_val = ""
                    marksheet = Marksheet.objects.filter(student=student.user, semester=semester).first()
                    if marksheet:
                       m_obj = Marks.objects.filter(marksheet=marksheet, subject=subject).first()
                       if m_obj: current_val = m_obj.marks
                    
                    student_list.append({'profile': student, 'current_marks': current_val})
                    
                context['student_list'] = student_list
            
        except Subject.DoesNotExist:
            messages.error(request, "Subject not found.")

    return render(request, 'marksheet/teacher_entry.html', context)



# ===================================
# 3. Student View: My Marksheet
# ===================================
@login_required
def student_my_marksheet(request):
    """
    Student marksheet view - students can view their own, admins can view any student's marksheet
    """
    # Check user role
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found.")
        return redirect('landing')
    
    user_institution = get_user_institution(request.user)
    
    # Determine which student's marksheet to show
    target_student_user = request.user  # Default to logged-in user
    
    if profile.role == 'student':
        # Students can only view their own marksheets
        target_student_user = request.user
    elif profile.role in ['institution_admin', 'teacher']:
        # Admins and teachers can view any student's marksheet within their institution
        student_id = request.GET.get('student_id')
        if student_id:
            try:
                target_student_user = User.objects.get(id=student_id)
                # Verify the user is actually a student AND belongs to the same institution
                if not hasattr(target_student_user, 'userprofile') or target_student_user.userprofile.role != 'student':
                    messages.error(request, "Invalid student selected.")
                    return redirect('landing')
                
                # Check institution match
                target_institution = get_user_institution(target_student_user)
                if target_institution != user_institution:
                    messages.error(request, "You do not have permission to view marksheets from another institution.")
                    return redirect('landing')

            except User.DoesNotExist:
                messages.error(request, "Student not found.")
                return redirect('landing')
        else:
            # If no student_id provided, redirect based on role
            if profile.role == 'institution_admin':
                return redirect('marksheet_admin')
            else:
                return redirect('teacher_enter_marks')
    else:
        messages.error(request, "Access denied.")
        return redirect('landing')
        
    marksheets = Marksheet.objects.filter(
        student=target_student_user,
        department__institution=user_institution
    ).prefetch_related(
        'marks', 
        'marks__subject'
    ).order_by('-semester')
    
    context = {
        'marksheets': marksheets,
        'viewing_student': target_student_user,
        'is_admin_view': profile.role in ['institution_admin', 'teacher'] and target_student_user != request.user
    }
    
    return render(request, 'marksheet/student_view.html', context)

@login_required
def generate_bulk_marksheets(request):
    """
    Teacher marksheet generator - step 1: Select department, subject, and semester
    """
    # Debug: Add logging
    print(f"🔍 DEBUG: User {request.user.username} accessing marksheet generator")
    
    # Check user role - must be teacher or admin
    try:
        profile = request.user.userprofile
        print(f"🔍 DEBUG: User role: {profile.role}")
        if profile.role not in ['teacher', 'institution_admin']:
            messages.error(request, "Access denied. Teacher privileges required.")
            return redirect('landing')
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found.")
        return redirect('landing')
        
    # Handle Student Request (Self-generation) - redirect to student view
    if profile.role == 'student':
        return redirect('student_marksheet')
    
    institution = get_user_institution(request.user)
    
    if not institution:
        messages.error(request, "Associated institution not found.")
        return redirect('landing')

    # Initialize defaults
    departments = Department.objects.none()
    dept_subjects = {}
    
    # Get departments based on role
    try:
        if profile.role in ['institution_admin', 'teacher']:
            # Both Admins and Teachers can see all departments in their institution
            departments = Department.objects.filter(institution=institution).order_by('name')
        else:
            # Fallback for any other roles (though handled above)
            departments = Department.objects.none()
            
        # Get subject mapping (optional helper data)
        assigned_subjects = TeacherSubject.objects.filter(
            teacher=request.user
        ).select_related('subject', 'subject__department')
        
        valid_subjects = assigned_subjects.filter(subject__department__isnull=False)
            
        # Group subjects by department for better UX
        for ts in valid_subjects:
            dept = ts.subject.department
            if dept and dept.id:
                if dept.id not in dept_subjects:
                    dept_subjects[dept.id] = {
                        'dept': {'id': dept.id, 'name': dept.name},
                        'subjects': []
                    }
                dept_subjects[dept.id]['subjects'].append({
                    'id': ts.subject.id,
                    'code': ts.subject.code,
                    'name': ts.subject.name
                })
            
    except Exception as e:
        messages.error(request, f"Error loading department data: {str(e)}")
        departments = Department.objects.none()
        dept_subjects = {}

    if request.method == 'POST':
        dept_id = request.POST.get('department_id')
        num_subjects = request.POST.get('num_subjects')
        semester = request.POST.get('semester')
        academic_year = request.POST.get('academic_year', '2025-2026')

        if not all([dept_id, num_subjects, semester]):
            messages.error(request, 'Please select department, number of subjects, and semester.')
        else:
            try:
                # Redirect to marks entry sheet 
                return redirect('marksheet_entry_sheet', 
                              dept_id=dept_id, 
                              num_subjects=num_subjects, 
                              semester=semester, 
                              academic_year=academic_year)
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')

    context = {
        'departments': departments,
        'semesters': range(1, 9),  # 8 semesters
    }
    return render(request, 'marksheet/teacher_generator.html', context)


@login_required
def marksheet_entry_sheet(request, dept_id, num_subjects, semester, academic_year):
    """
    Display and process marks entry sheet for all students in a department with N subject columns
    """
    try:
        profile = request.user.userprofile
        if profile.role not in ['teacher', 'institution_admin']:
            messages.error(request, "Access denied.")
            return redirect('landing')
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found.")
        return redirect('landing')
    
    institution = get_user_institution(request.user)
    
    try:
        department = Department.objects.get(id=dept_id, institution=institution)
        semester = int(semester)
        num_subjects = int(num_subjects)
        
        # Get all students in this department
        students = Student.objects.filter(
            department=department
        ).select_related('user').order_by('student_id')
        
        # Get all available subjects for this department to populate column dropdowns
        available_subjects = Subject.objects.filter(department=department).order_by('name')
        
        # Optimized: Create or get marksheets for all students efficiently
        student_user_ids = [s.user_id for s in students]
        existing_marksheets = Marksheet.objects.filter(
            student_id__in=student_user_ids,
            semester=semester,
            academic_year=academic_year
        )
        marksheet_map = {m.student_id: m for m in existing_marksheets}
        
        marksheets_to_create = []
        for student in students:
            if student.user_id not in marksheet_map:
                marksheets_to_create.append(Marksheet(
                    student=student.user,
                    teacher=request.user,
                    department=department,
                    semester=semester,
                    academic_year=academic_year,
                    total_marks=0,
                    percentage=0.0,
                    final_grade='',
                    shared_with_students=False # Default to false until shared
                ))
        
        if marksheets_to_create:
            Marksheet.objects.bulk_create(marksheets_to_create)
            # Re-fetch
            existing_marksheets = Marksheet.objects.filter(
                student_id__in=student_user_ids,
                semester=semester,
                academic_year=academic_year
            )
            marksheet_map = {m.student_id: m for m in existing_marksheets}

        # Handle form submission
        if request.method == 'POST':
            action = request.POST.get('action')
            target_student_id = request.POST.get('target_student_id')
            
            # 1. Identify subjects for each column
            col_subjects = {} # col_index -> subject_id
            for i in range(1, num_subjects + 1):
                col_val = request.POST.get(f'subject_col_{i}')
                if col_val:
                    # Try to find subject by name (case insensitive) within this department
                    subject = Subject.objects.filter(department=department, name__iexact=col_val.strip()).first()
                    if subject:
                        col_subjects[i] = subject.id
                    else:
                        # Fallback: check if it's an ID (for legacy support or direct entry)
                        try:
                            subj_id = int(col_val)
                            if Subject.objects.filter(id=subj_id, department=department).exists():
                                col_subjects[i] = subj_id
                        except (ValueError, TypeError):
                            pass

            if not col_subjects and action != 'share' and action != 'save_single':
                messages.error(request, "Please select at least one subject for the columns.")
            else:
                if action == 'save_single' and target_student_id:
                    # Handle Individual Row Save (AJAX)
                    try:
                        marksheet = marksheet_map.get(int(target_student_id))
                        if not marksheet:
                            return JsonResponse({'status': 'error', 'message': 'Marksheet not found.'})
                        
                        updated_count = 0
                        for col_idx, subj_id in col_subjects.items():
                            marks_val = request.POST.get(f'marks_{target_student_id}_{col_idx}')
                            if marks_val is not None and marks_val.strip():
                                marks_int = int(float(marks_val))
                                if 0 <= marks_int <= 100:
                                    Marks.objects.update_or_create(
                                        marksheet=marksheet,
                                        subject_id=subj_id,
                                        defaults={'marks': marks_int}
                                    )
                                    updated_count += 1
                        
                        return JsonResponse({
                            'status': 'success', 
                            'message': f'Marks saved for this student ({updated_count} entries).'
                        })
                    except Exception as e:
                        return JsonResponse({'status': 'error', 'message': str(e)})

                with transaction.atomic():
                    updated_marks_count = 0
                    for student in students:
                        marksheet = marksheet_map.get(student.user_id)
                        if not marksheet: continue
                        
                        for col_idx, subj_id in col_subjects.items():
                            marks_val = request.POST.get(f'marks_{student.user_id}_{col_idx}')
                            if marks_val is not None and marks_val.strip():
                                try:
                                    marks_int = int(float(marks_val))
                                    if 0 <= marks_int <= 100:
                                        # Use update_or_create for marks record
                                        # (Note: calculate_stats is triggered in Marks.save())
                                        Marks.objects.update_or_create(
                                            marksheet=marksheet,
                                            subject_id=subj_id,
                                            defaults={'marks': marks_int}
                                        )
                                        updated_marks_count += 1
                                except (ValueError, TypeError):
                                    continue
                        
                        # Stats calculation is already triggered in Marks.save()
                        
                        # Handle Global Share Action
                        if action == 'share':
                            marksheet.shared_with_students = True
                            marksheet.save(update_fields=['shared_with_students'])

                    if action == 'share':
                        messages.success(request, f'Marks saved and shared with students and admin successfully!')
                    else:
                        messages.success(request, f'Successfully saved {updated_marks_count} marks entries.')
                    
                    return redirect(request.path)
        
        # Prepare Subject Slots (Subject 1, 2, ...)
        subject_slots = range(1, num_subjects + 1)
        
        # Fetch current marks for the grid
        # Optimized: Fetch all marks for these marksheets in one query
        all_marks = Marks.objects.filter(
            marksheet__in=marksheet_map.values()
        ).select_related('subject')
        
        # Map: student_id -> subject_id -> marks_val
        marks_grid = {}
        for m in all_marks:
            if m.marksheet.student_id not in marks_grid:
                marks_grid[m.marksheet.student_id] = {}
            marks_grid[m.marksheet.student_id][m.subject_id] = m.marks

        # Guess column subjects for display based on existing marks
        # We'll take the first student who has marks and use their subjects as column labels
        current_subject_names = {} # col_idx -> name
        slots_data = {} # col_idx -> {'id': id, 'name': name}
        
        if all_marks.exists():
            # Get unique subjects already in use
            used_subjects = {} # id -> name
            for m in all_marks:
                used_subjects[m.subject_id] = m.subject.name
            
            # Assign them to slots 1...N
            for idx, (subj_id, subj_name) in enumerate(used_subjects.items(), 1):
                if idx <= num_subjects:
                    current_subject_names[idx] = subj_name
                    slots_data[idx] = {'id': subj_id, 'name': subj_name}

        # Attach marks to students for easy slot-based lookup in template
        for student in students:
            student_marks = [] # list of marks in slot order
            for i in range(1, num_subjects + 1):
                mark_val = ""
                if i in slots_data:
                    subj_id = slots_data[i]['id']
                    mark_val = marks_grid.get(student.user_id, {}).get(subj_id, "")
                student_marks.append(mark_val)
            student.marks_by_slot = student_marks

        context = {
            'department': department,
            'semester': semester,
            'academic_year': academic_year,
            'num_subjects': num_subjects,
            'subject_slots': subject_slots,
            'available_subjects': available_subjects,
            'students': students,
            'current_subject_names': current_subject_names,
            'total_students': students.count()
        }
        
        return render(request, 'marksheet/marks_entry_sheet.html', context)
        
    except (Department.DoesNotExist, ValueError) as e:
        messages.error(request, f"Invalid parameters: {str(e)}")
        return redirect('generate_bulk_marksheets')
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('generate_bulk_marksheets')

@login_required
def manage_marksheets(request):
    """
    List unique marksheet groups for the teacher to manage (edit/delete)
    """
    try:
        profile = request.user.userprofile
        if profile.role not in ['teacher', 'institution_admin']:
            messages.error(request, "Access denied.")
            return redirect('landing')
    except UserProfile.DoesNotExist:
        return redirect('landing')

    institution = get_user_institution(request.user)

    # Get unique groups of marksheets for this institution
    if institution:
        query = Marksheet.objects.filter(department__institution=institution)
    else:
        # Fallback to only marksheets created by this user
        query = Marksheet.objects.filter(teacher=request.user)

    groups = query.values(
        'department_id', 'department__name', 'semester', 'academic_year'
    ).annotate(student_count=models.Count('id')).order_by('-academic_year', '-semester')

    return render(request, 'marksheet/manage_marksheets.html', {'groups': groups})

@login_required
def delete_marksheet_group(request, dept_id, semester, academic_year):
    """
    Delete all marksheets in a group
    """
    institution = get_user_institution(request.user)
    
    if request.method == 'POST':
        with transaction.atomic():
            if institution:
                # Filter group within the institution
                qs = Marksheet.objects.filter(
                    department__institution=institution,
                    department_id=dept_id,
                    semester=semester,
                    academic_year=academic_year
                )
            else:
                # Fallback to teacher ownership
                qs = Marksheet.objects.filter(
                    teacher=request.user,
                    department_id=dept_id,
                    semester=semester,
                    academic_year=academic_year
                )
            
            deleted_count, _ = qs.delete()
            messages.success(request, f"Successfully deleted {deleted_count} marksheets.")
    
    return redirect('manage_marksheets')

