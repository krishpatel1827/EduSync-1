from django.shortcuts import render, get_object_or_404
from .models import TimetableEntry, Division, TimeSlot, Faculty, Subject, Room, Timetable
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

def dashboard(request):
    return render(request, 'dashboard.html')

def history(request):
    timetables = Timetable.objects.all().order_by('-created_at')
    return render(request, 'history.html', {'timetables': timetables})

def history_delete(request, timetable_id):
    timetable = get_object_or_404(Timetable, id=timetable_id)
    timetable.delete()
    messages.success(request, "Timetable deleted successfully!")
    return redirect('history')

def timetable_view(request, timetable_id=None):
    if timetable_id:
        timetable = get_object_or_404(Timetable, id=timetable_id)
    else:
        timetable = Timetable.objects.filter(is_active=True).first()
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

    subjects = Subject.objects.filter(timetableentry__timetable=timetable).distinct()
    faculties = Faculty.objects.filter(timetableentry__timetable=timetable).distinct()
    
    # Calculate colspan for break row: Time (1) + 3 columns per division
    break_colspan = (divisions.count() * 3) + 1

    context = {
        'divisions': divisions,
        'timetable_data': timetable_data,
        'current_timetable': timetable,
        'subjects': subjects,
        'faculties': faculties,
        'break_colspan': break_colspan,
    }
    return render(request, 'timetable.html', context)

@login_required
@never_cache
def add_entry(request):
    active_tt = Timetable.objects.filter(is_active=True).order_by('-created_at').first()
    
    if not active_tt:
        messages.error(request, "No active timetable found. Please generate one first.")
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
            
            days_count = form.cleaned_data.get('days_count', 6)
            new_tt = Timetable.objects.create(
                name=f"Timetable {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
                days_count=days_count
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
