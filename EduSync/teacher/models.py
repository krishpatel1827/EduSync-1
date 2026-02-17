from django.db import models
from django.contrib.auth.models import User
from institution.models import Institution

class Teacher(models.Model):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]
    CONTRACT_CHOICES = [('Full-Time', 'Full-Time'), ('Part-Time', 'Part-Time'), ('Contract', 'Contract'), ('Guest', 'Guest')]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, db_index=True)
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey('institution.Department', on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    qualification = models.CharField(max_length=200)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M')
    date_of_birth = models.DateField(null=True, blank=True)
    hire_date = models.DateField(auto_now_add=True)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    contract_type = models.CharField(max_length=20, choices=CONTRACT_CHOICES, default='Full-Time')
    photo = models.ImageField(upload_to='teachers/', blank=True, null=True)
    
    @property
    def initials(self):
        full_name = self.user.get_full_name()
        if not full_name:
            return self.user.username[:3].upper()
        return "".join([n[0].upper() for n in full_name.split() if n])

    def __str__(self):
        return f"{self.employee_id} - {self.user}"
