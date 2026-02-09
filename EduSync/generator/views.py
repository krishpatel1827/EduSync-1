from django.shortcuts import render, get_object_or_404
from .models import TimetableEntry, Division, TimeSlot, Room, Timetable
from academics.models import Course
from teacher.models import Teacher
from institution.models import Institution
from .forms import TimetableEntryForm, SetupForm
from django.shortcuts import redirect, render
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import datetime
import openpyxl
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

from accounts.utils import get_user_institution


def dashboard(request):
    return render(request, 'dashboard.html')

def history(request):
    institution = get_user_institution(request.user)
    timetables = Timetable.objects.filter(institution=institution).order_by('-created_at')
    return render(request, 'history.html', {'timetables': timetables})

def history_delete(request, timetable_id):
    institution = get_user_institution(request.user)
    timetable = get_object_or_404(Timetable, id=timetable_id, institution=institution)
    timetable.delete()
    messages.success(request, "Timetable deleted successfully!")
    return redirect('history')

def timetable_view(request, timetable_id=None):
    institution = get_user_institution(request.user)
    if timetable_id:
        timetable = get_object_or_404(Timetable, id=timetable_id, institution=institution)
    else:
        timetable = Timetable.objects.filter(institution=institution, is_active=True).first()
        if not timetable:
            return redirect('dashboard') 
            
    divisions = Division.objects.filter(timetable=timetable)
    timeslots = TimeSlot.objects.filter(timetable=timetable).order_by('lecture_number')

    # Dynamic Days Generation based on days_count
    all_days = [
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
        ('SAT', 'Saturday'),
        ('SUN', 'Sunday'),
    ]
    # Limit to the configured number of days
    days = all_days[:timetable.days_count]

    timetable_data = []

    for day_code, day_name in days:
        day_slots = []
        for slot in timeslots:
            # For each slot, get entries for all divisions
            slot_entries = {}
            for div in divisions:
                entry = TimetableEntry.objects.filter(
                    timetable=timetable,
                    day=day_code,
                    timeslot=slot,
                    division=div
                ).first()
                slot_entries[div.id] = entry
            day_slots.append({
                'slot': slot,
                'entries': slot_entries
            })
        
        timetable_data.append({
            'day_code': day_code,
            'day_name': day_name,
            'slots': day_slots
        })

    subjects = Course.objects.filter(timetableentry__timetable=timetable).distinct()
    faculties = Teacher.objects.filter(timetableentry__timetable=timetable).distinct()
    
    # Calculate colspan for break row: Time (1) + 3 columns per division
    break_colspan = (divisions.count() * 3) + 1

    context = {
        'divisions': divisions,
        'timetable_data': timetable_data,
        'current_timetable': timetable,
        'subjects': subjects,
        'faculties': faculties,
        'break_colspan': break_colspan,
        'header_form': None,
    }
    
    if timetable:
        from .forms import TimetableHeaderForm
        context['header_form'] = TimetableHeaderForm(instance=timetable)
        
    return render(request, 'timetable.html', context)

@login_required
@never_cache
def add_entry(request):
    institution = get_user_institution(request.user)
    active_tt = Timetable.objects.filter(institution=institution, is_active=True).order_by('-created_at').first()
    
    if not active_tt:
        messages.error(request, f"No active timetable found for {institution.name if institution else 'your institution'}. Please generate one first.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = TimetableEntryForm(request.POST, timetable=active_tt)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.timetable = active_tt
            entry.save()
            messages.success(request, "Entry added successfully!")
            return redirect('timetable')
    else:
        form = TimetableEntryForm(timetable=active_tt)
    
    return render(request, 'entry_form.html', {'form': form})

@login_required
@never_cache
def setup_view(request):
    if request.method == 'POST':
        form = SetupForm(request.POST)
        if form.is_valid():
            # Create NEW Timetable
            Timetable.objects.filter(is_active=True).update(is_active=False)
            
            institution = get_user_institution(request.user)
            days_count = form.cleaned_data.get('days_count', 6)
            new_tt = Timetable.objects.create(
                name=f"Timetable {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
                days_count=days_count,
                institution=institution
            )
            
            # Process Divisions
            div_names = [d.strip() for d in form.cleaned_data['divisions'].split(',') if d.strip()]
            for name in div_names:
                Division.objects.create(name=name, timetable=new_tt)
            
            # Process TimeSlots
            start_time = form.cleaned_data['start_time']
            slot_duration = form.cleaned_data['slot_duration']
            break_duration = form.cleaned_data['break_duration']
            slots_before = form.cleaned_data['slots_before_break']
            slots_after = form.cleaned_data['slots_after_break']
            
            current_time = datetime.datetime.combine(datetime.date.today(), start_time)
            lecture_num = 1
            
            # First batch of lectures
            for _ in range(slots_before):
                end_time = current_time + datetime.timedelta(minutes=slot_duration)
                TimeSlot.objects.create(
                    timetable=new_tt,
                    lecture_number=lecture_num,
                    start_time=current_time.time(),
                    end_time=end_time.time()
                )
                current_time = end_time
                lecture_num += 1
            
            # Break - Only create if duration > 0
            if break_duration and break_duration > 0:
                break_end = current_time + datetime.timedelta(minutes=break_duration)
                TimeSlot.objects.create(
                    timetable=new_tt,
                    lecture_number=lecture_num, 
                    start_time=current_time.time(),
                    end_time=break_end.time(),
                    is_break=True
                )
                current_time = break_end
                # Note: We usually increment lecture number or keep it unique?
                # The existing code didn't seem to increment lecture_num for break in a way that affects display,
                # but let's consistency increment it so ordering works.
                lecture_num += 1
            
            # Second batch
            for _ in range(slots_after):
                end_time = current_time + datetime.timedelta(minutes=slot_duration)
                TimeSlot.objects.create(
                    timetable=new_tt,
                    lecture_number=lecture_num,
                    start_time=current_time.time(),
                    end_time=end_time.time()
                )
                current_time = end_time
                lecture_num += 1
            
            messages.success(request, "New Timetable Structure Generated Successfully!")
            return redirect('timetable', timetable_id=new_tt.id)
    else:
        form = SetupForm()
    
    return render(request, 'setup.html', {'form': form})

def export_excel(request, timetable_id):
    timetable = get_object_or_404(Timetable, id=timetable_id)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{timetable.name}.xlsx"'
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Timetable"
    
    # Headers
    divisions = Division.objects.filter(timetable=timetable)
    headers = ["Day", "Slot"] + [d.name for d in divisions]
    ws.append(headers)
    
    # Data
    days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']
    timeslots = TimeSlot.objects.filter(timetable=timetable).order_by('lecture_number')
    
    for day in days:
        for slot in timeslots:
            row = [day, f"{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}"]
            if slot.is_break:
                row.append("BREAK")
                # Merge? simplistic for now
            else:
                for div in divisions:
                    entry = TimetableEntry.objects.filter(timetable=timetable, day=day, timeslot=slot, division=div).first()
                    if entry:
                        cell_val = f"{entry.subject.code}\n{entry.faculty.initials}\n{entry.room.number}"
                    else:
                        cell_val = ""
                    row.append(cell_val)
            ws.append(row)
            
    wb.save(response)
    return response

def export_pdf(request, timetable_id):
    timetable = get_object_or_404(Timetable, id=timetable_id)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{timetable.name}.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=landscape(letter))
    elements = []
    
    data = []
    # Headers
    divisions = list(Division.objects.filter(timetable=timetable))
    headers = ["Day", "Time"] + [d.name for d in divisions]
    data.append(headers)
    
    # Data
    days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']
    timeslots = TimeSlot.objects.filter(timetable=timetable).order_by('lecture_number')
    
    for day in days:
        for slot in timeslots:
            row = [day, f"{slot.start_time.strftime('%H:%M')}-{slot.end_time.strftime('%H:%M')}"]
            if slot.is_break:
                row.extend(["BREAK"] * len(divisions))
            else:
                for div in divisions:
                    entry = TimetableEntry.objects.filter(timetable=timetable, day=day, timeslot=slot, division=div).first()
                    if entry:
                        row.append(f"{entry.subject.code}\n{entry.faculty.initials}\n{entry.room.number}")
                    else:
                        row.append("-")
            data.append(row)
            
    # Table Styling
    t = Table(data)
    style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTSIZE', (0,0), (-1,-1), 8),
    ])
    t.setStyle(style)
    elements.append(t)
    doc.build(elements)
    
    return response

@login_required
@never_cache
def auto_generate_timetable(request, timetable_id):
    institution = get_user_institution(request.user)
    timetable = get_object_or_404(Timetable, id=timetable_id, institution=institution)
    
    # 1. Clear existing entries for this timetable to start fresh (optional, but safer for "auto-gen")
    # removing this if we want to fill *only empty* slots, but user said "all the fields should be field"
    # Let's clear to avoid conflicts with manual entries if they want a full regen.
    # checking if user wants to keep manual? assuming overwrite for "auto gen".
    timetable.entries.all().delete()
    
    # 2. Get Resources
    courses = list(Course.objects.filter(institution=institution))
    teachers = list(Teacher.objects.filter(institution=institution))
    # We need rooms. If no rooms exist, create some dummy ones or error?
    # Let's check if Room model exists and has data.
    rooms = list(Room.objects.filter(institution=institution))
    
    if not courses or not teachers:
        messages.error(request, "Not enough courses or teachers to generate timetable.")
        return redirect('timetable', timetable_id=timetable.id)
        
    if not rooms:
        # Create some default rooms if none exist
        for i in range(101, 111):
            Room.objects.create(institution=institution, number=str(i))
        rooms = list(Room.objects.filter(institution=institution))

    divisions = Division.objects.filter(timetable=timetable)
    timeslots = TimeSlot.objects.filter(timetable=timetable, is_break=False)
    days_data = [
        ('MON', 'Monday'), ('TUE', 'Tuesday'), ('WED', 'Wednesday'), 
        ('THU', 'Thursday'), ('FRI', 'Friday'), ('SAT', 'Saturday'), ('SUN', 'Sunday')
    ][:timetable.days_count]
    
    import random

    # Track usage to prevent conflicts
    # teacher_schedule[(day, timeslot_id)] = teacher_id
    # room_schedule[(day, timeslot_id)] = room_id
    teacher_occupation = {}
    room_occupation = {}

    entries_created = 0

    for day_code, _ in days_data:
        for slot in timeslots:
            for div in divisions:
                # Attempt to assign a random course, teacher, and room
                # Try X times to find a non-conflicting combination
                attempts = 0
                max_attempts = 50
                success = False
                
                while attempts < max_attempts:
                    course = random.choice(courses)
                    teacher = random.choice(teachers) #Ideally course.teachers.all() but valid logic might be complex
                    room = random.choice(rooms)
                    
                    # Check Teacher Conflict
                    if teacher_occupation.get((day_code, slot.id)) == teacher.id:
                        attempts += 1
                        continue
                        
                    # Check Room Conflict
                    if room_occupation.get((day_code, slot.id)) == room.id:
                        attempts += 1
                        continue
                    
                    # No Conflict! Assign
                    TimetableEntry.objects.create(
                        timetable=timetable,
                        day=day_code,
                        timeslot=slot,
                        division=div,
                        subject=course,
                        faculty=teacher,
                        room=room
                    )
                    
                    teacher_occupation[(day_code, slot.id)] = teacher.id
                    room_occupation[(day_code, slot.id)] = room.id
                    entries_created += 1
                    success = True
                    break
                
                if not success:
                    # Could not find a valid slot (maybe shortage of teachers/rooms)
                    # Use a placeholder or leave empty?
                    # Leaving empty is safer than invalid data
                    pass

    messages.success(request, f"Auto-generated {entries_created} timetable entries successfully!")
    return redirect('timetable', timetable_id=timetable.id)

@login_required
@never_cache
def clear_timetable_entries(request, timetable_id):
    institution = get_user_institution(request.user)
    timetable = get_object_or_404(Timetable, id=timetable_id, institution=institution)
    
    if request.method == "POST":
        count = timetable.entries.count()
        timetable.entries.all().delete()
        messages.success(request, f"Cleared {count} entries from the timetable.")
        
    return redirect('timetable', timetable_id=timetable.id)

@login_required
@never_cache
def edit_timetable_header(request, timetable_id):
    institution = get_user_institution(request.user)
    timetable = get_object_or_404(Timetable, id=timetable_id, institution=institution)
    
    if request.method == "POST":
        from .forms import TimetableHeaderForm
        form = TimetableHeaderForm(request.POST, instance=timetable)
        if form.is_valid():
            form.save()
            messages.success(request, "Timetable headers updated successfully!")
        else:
            messages.error(request, "Error updating headers.")
            
    return redirect('timetable', timetable_id=timetable.id)

@login_required
@never_cache
def toggle_theme(request, timetable_id):
    institution = get_user_institution(request.user)
    timetable = get_object_or_404(Timetable, id=timetable_id, institution=institution)
    
    themes = ['classic', 'modern_blue', 'nature_green', 'sunset_orange', 'minimal_dark']
    
    # Simple cycling
    try:
        current_index = themes.index(timetable.theme_palette)
        next_index = (current_index + 1) % len(themes)
    except ValueError:
        next_index = 0
        
    timetable.theme_palette = themes[next_index]
    timetable.save()
    
    messages.success(request, f"Theme changed to {themes[next_index].replace('_', ' ').title()}!")
    return redirect('timetable', timetable_id=timetable.id)
