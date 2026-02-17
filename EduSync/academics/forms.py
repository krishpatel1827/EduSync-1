from django import forms
from .models import Course


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

