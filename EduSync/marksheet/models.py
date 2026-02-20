from django.db import models
from django.contrib.auth.models import User
from institution.models import Department
from academics.models import Course
from teacher.models import Teacher

# Note: Using existing Student model from student app, no need for separate StudentProfile

# ===================================
# 1. TeacherSubject  
# ===================================
class TeacherSubject(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_subjects')
    # Link to existing Course model instead of new Subject model
    subject = models.ForeignKey(Course, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('teacher', 'subject')
        
    def __str__(self):
        # Course has 'name' and 'code'
        return f"{self.teacher.username} -> {self.subject.name}"

# ===================================
# 4. Marksheet
# ===================================
class Marksheet(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='marksheets')
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_marksheets')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='marksheets')
    semester = models.IntegerField()
    academic_year = models.CharField(max_length=20)
    total_marks = models.IntegerField(default=0)
    percentage = models.FloatField(default=0.0)
    final_grade = models.CharField(max_length=5, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    shared_with_students = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('student', 'semester', 'academic_year')
        
    def __str__(self):
        return f"{self.student.username} - Sem {self.semester} ({self.academic_year})"
        
    def calculate_stats(self):
        """
        Recalculates total marks, percentage, and final grade based on related Marks.
        """
        marks_qs = self.marks.all()
        if not marks_qs.exists():
            return

        total_obtained = sum(m.marks for m in marks_qs)
        # Assuming Course model has a max_marks field? 
        # Checking academics.models.py... Course has 'credits' but NOT 'max_marks'.
        # We might need to handle this. For now, let's assume 100 per course or add a field if allowed?
        # User said "Do NOT rewrite or modify existing project structure." -> We cannot add fields to Course easily without migration there.
        # But we create a new app. We can add a 'max_marks' to the 'Marks' model default or config?
        # Or better, we assume 100 for now as per previous logic, or defined in TeacherSubject?
        # Let's iterate: The previous Subject model had max_marks. Existing Course does not.
        # We can add a "CourseMetadata" in marksheet app or just hardcode/assume 100 for simplicity as allowed.
        # Or, we can add 'max_marks' to the Marks model (e.g. out of 100).
        
        # We will use 100 as default max marks for calculation since we cannot modify Course model.
        total_max = marks_qs.count() * 100 
        
        self.total_marks = total_obtained
        self.percentage = (total_obtained / total_max * 100) if total_max > 0 else 0
        self.final_grade = get_grade(self.percentage)
        self.save()

        # Update student GPA (out of 10)
        from student.models import Student
        student_obj = Student.objects.filter(user=self.student).first()
        if student_obj:
            all_marksheets = Marksheet.objects.filter(student=self.student)
            if all_marksheets.exists():
                avg_percentage = all_marksheets.aggregate(models.Avg('percentage'))['percentage__avg']
                student_obj.gpa = round(avg_percentage / 10.0, 2)
                student_obj.save(update_fields=['gpa'])

# ===================================
# Grade Calculation Helper
# ===================================
def get_grade(marks_percentage):
    if marks_percentage >= 90: return 'A+'
    elif marks_percentage >= 80: return 'A'
    elif marks_percentage >= 70: return 'B+'
    elif marks_percentage >= 60: return 'B'
    elif marks_percentage >= 50: return 'C'
    elif marks_percentage >= 40: return 'D'
    else: return 'F'

# ===================================
# 5. Marks
# ===================================
class Marks(models.Model):
    marksheet = models.ForeignKey(Marksheet, on_delete=models.CASCADE, related_name='marks')
    # Link to existing Course
    subject = models.ForeignKey(Course, on_delete=models.CASCADE)
    marks = models.IntegerField()
    grade = models.CharField(max_length=5, blank=True)
    
    class Meta:
        unique_together = ('marksheet', 'subject')
        
    def save(self, *args, **kwargs):
        # Calculate grade for this subject based on percentage
        # Assuming max_marks = 100 for standard courses
        percentage = (self.marks / 100) * 100 
        self.grade = get_grade(percentage)
        super().save(*args, **kwargs)
        # Trigger parent marksheet update
        self.marksheet.calculate_stats()

    def __str__(self):
        return f"{self.marksheet.student.username} - {self.subject.name}: {self.marks}"
