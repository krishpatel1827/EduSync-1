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
        timetable = self.instance.timetable if self.instance.timetable else self.fields['timeslot'].queryset.first().timetable if self.fields['timeslot'].queryset.exists() else None
        
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
            
            # 3. Check Division Conflict (Already handled by unique constraint usually, but good to be explicit)
            if division:
                qs = TimetableEntry.objects.filter(timetable=timetable, day=day, timeslot=timeslot, division=division)
                if self.instance.pk:
                    qs = qs.exclude(pk=self.instance.pk)
                if qs.exists():
                    raise forms.ValidationError(f"Division {division} already has a class at this time.")

        return cleaned_data

class SetupForm(forms.Form):
    divisions = forms.CharField(label="Divisions (Comma separated, e.g., D1, D2)", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'D1, D2, D3'}))
    days_count = forms.IntegerField(label="Number of Days (e.g., 5 or 6)", initial=6, min_value=1, max_value=7, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    start_time = forms.TimeField(label="First Lecture Start Time", widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time', 'value': '08:45'}))
    slot_duration = forms.IntegerField(label="Lecture Duration (Minutes)", initial=60, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    break_duration = forms.IntegerField(label="Break Duration (Minutes)", initial=45, required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter 0 for NO BREAK'}))
    
    # Simple configuration: How many slots before break?
    # Let's assume a pattern: x lectures, break, y lectures.
    slots_before_break = forms.IntegerField(label="Lectures before break", initial=2, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    slots_after_break = forms.IntegerField(label="Lectures after break", initial=2, widget=forms.NumberInput(attrs={'class': 'form-control'}))


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

