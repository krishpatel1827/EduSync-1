from django import forms
from .models import TimetableEntry, TimeSlot, Division, Room
from academics.models import Course
from teacher.models import Teacher

class TimetableEntryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        timetable = kwargs.pop('timetable', None)
        # We can also pass institution directly if we want to be more explicit
        institution = getattr(timetable, 'institution', None)
        
        super().__init__(*args, **kwargs)
        self.timetable = timetable
        if timetable:
            self.instance.timetable = timetable
        
        if timetable:
            self.fields['timeslot'].queryset = TimeSlot.objects.filter(timetable=timetable)
            self.fields['division'].queryset = Division.objects.filter(timetable=timetable)
            
            # CRITICAL: Always filter by institution to prevent cross-institution data exposure
            if institution:
                self.fields['subject'].queryset = Course.objects.filter(institution=institution)
                self.fields['faculty'].queryset = Teacher.objects.filter(institution=institution)
                self.fields['room'].queryset = Room.objects.filter(institution=institution)
            else:
                # If no institution is linked to the timetable, show nothing to be safe
                self.fields['subject'].queryset = Course.objects.none()
                self.fields['faculty'].queryset = Teacher.objects.none()
                self.fields['room'].queryset = Room.objects.none()
        else:
            self.fields['timeslot'].queryset = TimeSlot.objects.none()
            self.fields['division'].queryset = Division.objects.none()
            self.fields['subject'].queryset = Course.objects.none()
            self.fields['faculty'].queryset = Teacher.objects.none()
            self.fields['room'].queryset = Room.objects.none()

    class Meta:
        model = TimetableEntry
        fields = ['day', 'timeslot', 'division', 'subject', 'faculty', 'room']
        widgets = {
            'day': forms.Select(attrs={'class': 'form-control'}),
            'timeslot': forms.Select(attrs={'class': 'form-control'}),
            'division': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'faculty': forms.Select(attrs={'class': 'form-control'}),
            'room': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        
        # Get timetable from stored property or instance
        timetable = getattr(self, 'timetable', None)
        if not timetable:
            try:
                timetable = self.instance.timetable
            except Exception:
                timetable = None
        
        # If we are in add view, we passed timetable in init, but in django ModelForm proper way is to look at instance or context.
        # However, checking duplicates:
        day = cleaned_data.get('day')
        timeslot = cleaned_data.get('timeslot')
        faculty = cleaned_data.get('faculty')
        room = cleaned_data.get('room')
        division = cleaned_data.get('division')
        
        # We need the timetable context. `add_entry` sets instance.timetable effectively? No, it sets it after save.
        # But we filter querysets by timetable. So we can grab it from there.
        if not timetable and hasattr(self, 'fields') and self.fields['timeslot'].queryset.exists():
             timetable = self.fields['timeslot'].queryset.first().timetable

        if day and timeslot and timetable:
            # 1. Check Faculty Conflict
            if faculty:
                # Exclude self if editing
                qs = TimetableEntry.objects.filter(timetable=timetable, day=day, timeslot=timeslot, faculty=faculty)
                if self.instance.pk:
                    qs = qs.exclude(pk=self.instance.pk)
                if qs.exists():
                   conflicting_entry = qs.first()
                   raise forms.ValidationError(f"Faculty {faculty} is already booked in {conflicting_entry.division} at this time ({day} {timeslot}).")

            # 2. Check Room Conflict
            if room:
                qs = TimetableEntry.objects.filter(timetable=timetable, day=day, timeslot=timeslot, room=room)
                if self.instance.pk:
                   qs = qs.exclude(pk=self.instance.pk)
                if qs.exists():
                   conflicting_entry = qs.first()
                   raise forms.ValidationError(f"Room {room} is already occupied by {conflicting_entry.division} at this time ({day} {timeslot}).")
            
            # 3. Check for Redundancy vs Collision
            if division:
                existing = TimetableEntry.objects.filter(
                    timetable=timetable, day=day, timeslot=timeslot, division=division
                ).first()
                
                if existing:
                    # Check if redundant (all inputs same)
                    is_redundant = (
                        existing.subject == cleaned_data.get('subject') and
                        existing.faculty == cleaned_data.get('faculty') and
                        existing.room == cleaned_data.get('room')
                    )
                    if is_redundant:
                        raise forms.ValidationError(f"Redundant Entry: This exact schedule already exists for {division} at this time.")
                    
                    # If not redundant, we allow it (the view handles this by providing the instance)
                    pass

        return cleaned_data

class SetupForm(forms.Form):
    from institution.models import Department
    
    department = forms.ModelChoiceField(
        queryset=Department.objects.none(),
        required=False,
        label="Department (Optional)",
        help_text="Assign to a specific department, or leave blank for institution-wide",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    course = forms.ModelChoiceField(
        queryset=Course.objects.none(),
        required=False,
        label="Course/Branch (Optional)",
        help_text="Assign to a specific course, or leave blank for department-wide",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    divisions = forms.CharField(label="Divisions (Comma separated, e.g., D1, D2)", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'D1, D2, D3'}))
    days_count = forms.IntegerField(label="Number of Days (e.g., 5 or 6)", initial=6, min_value=1, max_value=7, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    start_time = forms.TimeField(label="First Lecture Start Time", widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time', 'value': '08:45'}))
    slot_duration = forms.IntegerField(label="Lecture Duration (Minutes)", initial=60, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    break_duration = forms.IntegerField(label="Break Duration (Minutes)", initial=45, required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter 0 for NO BREAK'}))
    
    # Simple configuration: How many slots before break?
    # Let's assume a pattern: x lectures, break, y lectures.
    slots_before_break = forms.IntegerField(label="Lectures before break", initial=2, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    slots_after_break = forms.IntegerField(label="Lectures after break", initial=2, widget=forms.NumberInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, institution=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        from institution.models import Department
        
        if institution:
            # Set department queryset based on institution
            self.fields['department'].queryset = Department.objects.filter(institution=institution)
            self.fields['course'].queryset = Course.objects.filter(institution=institution)
            
            # If user is a teacher, auto-select and restrict to their department
            if user and hasattr(user, 'teacher'):
                try:
                    teacher = user.teacher
                    if teacher.department:
                        self.fields['department'].queryset = Department.objects.filter(id=teacher.department.id)
                        self.fields['department'].initial = teacher.department
                        # Filter courses by teacher's department
                        self.fields['course'].queryset = Course.objects.filter(
                            institution=institution,
                            department=teacher.department
                        )
                except Exception:
                    pass
        else:
            self.fields['department'].queryset = Department.objects.none()
            self.fields['course'].queryset = Course.objects.none()
    
    def clean(self):
        cleaned_data = super().clean()
        department = cleaned_data.get('department')
        course = cleaned_data.get('course')
        
        # If course is selected, department must also be selected
        if course and not department:
            raise forms.ValidationError("Please select a department when assigning a course.")
        
        # Verify course belongs to selected department (if both are set)
        if department and course:
            if hasattr(course, 'department') and course.department:
                if course.department.id != department.id:
                    raise forms.ValidationError("Selected course does not belong to the selected department.")
        
        return cleaned_data


class TimetableHeaderForm(forms.ModelForm):
    class Meta:
        from .models import Timetable
        model = Timetable
        fields = ['heading_1', 'heading_2', 'name', 'footer_semester_text', 'footer_prepared_by', 'footer_hod']
        labels = {
            'heading_1': 'Main Header (Institution)',
            'heading_2': 'Sub Header (Department)',
            'name': 'Timetable Title (e.g. SEM-III ...)',
            'footer_semester_text': 'Footer Title (e.g. SEMESTER III)',
            'footer_prepared_by': 'Prepared By text (Signatures)',
            'footer_hod': 'HOD Signature text',
        }
        widgets = {
            'heading_1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. L.J. INSTITUTE...'}),
            'heading_2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. SY CE/IT...'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Timetable Name'}),
            'footer_semester_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SEMESTER ...'}),
            'footer_prepared_by': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'footer_hod': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class PublishTimetableForm(forms.Form):
    from institution.models import Department
    from academics.models import Branch

    name = forms.CharField(
        max_length=100,
        label="Timetable Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. SEM-III Timetable'})
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.none(),
        required=True,
        label="Department",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'publish-department'})
    )
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.none(),
        required=True,
        label="Branch",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'publish-branch'})
    )

    def __init__(self, *args, institution=None, timetable=None, **kwargs):
        super().__init__(*args, **kwargs)
        from institution.models import Department
        from academics.models import Branch

        if institution:
            self.fields['department'].queryset = Department.objects.filter(institution=institution)
            self.fields['branch'].queryset = Branch.objects.filter(institution=institution)

        if timetable:
            self.fields['name'].initial = timetable.name
            if timetable.department:
                self.fields['department'].initial = timetable.department
            if timetable.branch:
                self.fields['branch'].initial = timetable.branch

