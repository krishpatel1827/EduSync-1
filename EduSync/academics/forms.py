from django import forms
from .models import Course, AcademicCalendar, CalendarEvent
from institution.models import Department


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["code", "name", "description", "credits", "duration_months", "department", "tuition_fee"]
        widgets = {
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "credits": forms.NumberInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "department": forms.Select(attrs={"class": "form-control"}),
            "tuition_fee": forms.NumberInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, institution=None, **kwargs):
        super().__init__(*args, **kwargs)
        if institution:
            from institution.models import Department
            self.fields['department'].queryset = Department.objects.filter(institution=institution)


class AcademicCalendarForm(forms.ModelForm):
    department = forms.ModelChoiceField(
        queryset=Department.objects.none(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        label='Department',
        help_text='Optional — leave blank to make calendar available to all departments'
    )

    class Meta:
        model = AcademicCalendar
        # expose department + share flags so admins can set visibility from the edit form
        fields = ["semester", "year", "department", "shared_with_students", "shared_with_teachers"]
        widgets = {
            "semester": forms.TextInput(attrs={"class": "form-control", "placeholder": "Semester 1"}),
            "year": forms.TextInput(attrs={"class": "form-control", "placeholder": "2026-2027"}),
            "shared_with_students": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "shared_with_teachers": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        institution = kwargs.pop('institution', None)
        super().__init__(*args, **kwargs)
        # limit department choices to the user's institution when provided
        if institution:
            self.fields['department'].queryset = Department.objects.filter(institution=institution)
        else:
            self.fields['department'].queryset = Department.objects.all()


class CalendarEventForm(forms.ModelForm):
    # Optional end date lets admin create the same event across a date range (inclusive).
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}), help_text='Optional — create this event on every date from Date → End date')

    class Meta:
        model = CalendarEvent
        # simplified form: no free-text title/description — title will be derived from `type`
        fields = ["date", "end_date", "type", "color_code"]
        widgets = {
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            # make `type` editable (text input) but provide suggestions via datalist
            "type": forms.TextInput(attrs={"class": "form-control", "list": "event-type-suggestions", "event_type_choices": CalendarEvent.EVENT_TYPES}),
            "color_code": forms.TextInput(attrs={"class": "form-control", "type": "color", "value": "#2563EB"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # allow omission of color in POST; server will default it based on type
        self.fields['color_code'].required = False

        # prefer provided initial color -> instance color -> default by type
        provided = self.initial.get('color_code') or (getattr(self.instance, 'color_code', None) if hasattr(self, 'instance') else None)
        if not provided:
            type_key = self.initial.get('type') or (getattr(self.instance, 'type', None) if getattr(self.instance, 'pk', None) else None)
            if type_key:
                # use DB overrides when present
                self.fields['color_code'].initial = CalendarEvent.get_type_color_mapping().get(type_key, '#2563EB')

    def clean(self):
        cleaned = super().clean()
        color = cleaned.get('color_code')
        ev_type = cleaned.get('type')
        start_date = cleaned.get('date')
        end_date = cleaned.get('end_date')

        if end_date and start_date and end_date < start_date:
            raise forms.ValidationError('End date cannot be earlier than the start date.')

        if not color:
            # fill server-side default (DB override preferred)
            cleaned['color_code'] = CalendarEvent.color_for_type(ev_type)
        return cleaned

