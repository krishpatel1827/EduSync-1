# ================================================================================
# STUDENT APP - MODELS.PY
# ================================================================================
# This file defines the database structure for student management in EduSync.
# It contains the Student model which stores all information about enrolled students
# including personal details, academic information, and institutional relationships.
#
# WHAT IS A STUDENT IN EDUSYNC?
# A student is a person enrolled in courses at an educational institution.
# The Student model connects to Django's User system for authentication while
# storing additional academic and personal information specific to students.
#
# KEY RELATIONSHIPS:
# - Student ←→ User (One-to-One): Each student has one login account
# - Student ←→ Institution (Many-to-One): Students belong to one institution
# - Student ←→ Course (Many-to-One): Students can enroll in one main course/program
# - Student ←→ Branch (Many-to-One): Students are assigned to academic branches
# - Student ←→ Department (Many-to-One): Students belong to academic departments
# - Student ←→ Division (Many-to-One): Students are grouped into divisions for timetabling
#
# ACADEMIC HIERARCHY:
# Institution → Department → Branch → Course → Student → Division
# This hierarchy helps organize students into manageable academic groups.
# ================================================================================

# Import Django's database models and User authentication system
from django.db import models
from django.contrib.auth.models import User
# Import Institution model to establish institutional relationships
from institution.models import Institution


class Student(models.Model):
    """
    WHAT THIS MODEL REPRESENTS:
    The Student model stores comprehensive information about students enrolled
    in the educational institution. This includes personal details, academic
    information, enrollment data, and relationships to courses and programs.
    
    PURPOSE:
    - Manage student enrollment and registration
    - Track academic progress and performance
    - Organize students into classes and divisions
    - Maintain student contact and emergency information
    - Support academic reporting and analytics
    
    WHO HAS ACCESS:
    - Institution admins: Full access to all student data
    - Teachers: Access to students in their courses
    - Students: Access to their own data only
    - Parents: Limited access to their child's information (future feature)
    
    DATABASE TABLE NAME:
    This model uses a custom table name 'student_student' (defined in Meta class)
    """
    
    # CHOICE FIELDS: Predefined options for certain fields
    # These ensure data consistency and enable filtering/reporting
    
    # Student Status Options
    # Tracks whether student is currently active or has left/graduated
    STATUS_CHOICES = [
        ('active', 'Active'),     # Currently enrolled and attending
        ('inactive', 'Inactive'), # Graduated, transferred, or temporarily absent
    ]
    
    # Gender Options
    # Supports inclusive gender identification
    GENDER_CHOICES = [
        ('M', 'Male'),      # Male students
        ('F', 'Female'),    # Female students  
        ('O', 'Other'),     # Non-binary, prefer not to say, etc.
    ]
    
    # ============================================================================
    # AUTHENTICATION & INSTITUTIONAL RELATIONSHIPS
    # ============================================================================
    
    # FIELD: User Account Connection
    # OneToOneField links each student to exactly one Django User account
    # This provides login credentials and basic user information
    # on_delete=CASCADE means deleting User account also deletes Student record
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # FIELD: Institution Membership
    # ForeignKey links student to their educational institution
    # Enables multi-tenant system where each institution manages its own students
    # on_delete=CASCADE means deleting Institution also deletes all its students
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)
    
    # ============================================================================
    # ACADEMIC PROGRAM RELATIONSHIPS
    # ============================================================================
    
    # FIELD: Course/Program Enrollment
    # Links student to their main academic course or program
    # ForeignKey to 'academics.Course' (string reference to avoid import cycles)
    # SET_NULL means if course is deleted, student remains but course becomes null
    # db_index=True creates database index for faster queries
    course = models.ForeignKey('academics.Course', on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    
    # FIELD: Academic Branch Assignment
    # Links student to specific branch within their department
    # Examples: "Computer Science", "Electrical Engineering", "Biology"
    # SET_NULL preserves student record if branch is deleted
    branch = models.ForeignKey('academics.Branch', on_delete=models.SET_NULL, null=True, blank=True)
    
    # FIELD: Department Assignment  
    # Links student to academic department
    # Examples: "Engineering", "Science", "Arts", "Business"
    # SET_NULL preserves student record if department is deleted
    department = models.ForeignKey('institution.Department', on_delete=models.SET_NULL, null=True, blank=True)
    
    # FIELD: Division Assignment
    # Links student to division for timetable and class organization
    # Divisions are groups within a branch (like "Division A", "Division B")
    # Used for creating class schedules and managing classroom assignments
    division = models.ForeignKey('generator.Division', on_delete=models.SET_NULL, null=True, blank=True, help_text="Student's division for timetable")
    
    # ============================================================================
    # STUDENT IDENTIFICATION & CONTACT
    # ============================================================================
    
    # FIELD: Student ID Number
    # Unique identifier assigned by the institution
    # Examples: "ST001", "2024CS001", "STU123456"
    # unique=True ensures no two students have the same ID globally
    student_id = models.CharField(max_length=20, unique=True)
    
    # FIELD: Phone Number
    # Student's contact phone number
    # Optional field (blank=True) as not all students may have phones
    phone = models.CharField(max_length=15, blank=True)
    
    # FIELD: Home Address
    # Student's residential address for contact and emergency purposes
    # TextField allows for multi-line addresses
    # Optional but recommended for emergency contacts
    address = models.TextField(blank=True)
    
    # ============================================================================
    # PERSONAL INFORMATION
    # ============================================================================
    
    # FIELD: Gender Identity
    # Uses predefined choices for consistency
    # Default 'M' for backwards compatibility (can be changed during setup)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M')
    
    # FIELD: Date of Birth
    # Used for age verification, academic eligibility, and demographic reporting
    # Optional fields (null=True, blank=True) as this information may be sensitive
    date_of_birth = models.DateField(null=True, blank=True)
    
    # FIELD: Blood Group
    # Medical information for emergency situations
    # Examples: "A+", "B-", "O+", "AB-"
    # Optional field but important for health emergencies
    blood_group = models.CharField(max_length=5, blank=True)
    
    # ============================================================================
    # PARENT/GUARDIAN INFORMATION
    # ============================================================================
    
    # FIELD: Parent/Guardian Name
    # Primary contact person for the student
    # Used for emergency contacts and academic communications
    parent_name = models.CharField(max_length=150, blank=True)
    
    # FIELD: Parent/Guardian Phone
    # Emergency contact phone number
    # Critical for urgent communications and emergencies
    parent_phone = models.CharField(max_length=15, blank=True)
    
    # ============================================================================
    # ACADEMIC TRACKING & PROGRESS
    # ============================================================================
    
    # FIELD: Academic Year
    # Which academic year/batch the student belongs to
    # Examples: "2024-2025", "First Year", "Sophomore"
    # String field to accommodate different naming conventions
    academic_year = models.CharField(max_length=20, blank=True)
    
    # FIELD: Current Semester  
    # Which semester the student is currently in
    # IntegerField with default value of 3 (can be adjusted)
    # help_text provides guidance for users entering data
    semester = models.IntegerField(default=3, help_text="Current semester (1-8)")
    
    # FIELD: Grade Point Average (GPA)
    # Student's cumulative academic performance
    # FloatField allows decimal values (e.g., 3.75, 2.50)
    # Default 0.0 for new students who haven't received grades yet
    gpa = models.FloatField(default=0.0)
    
    # FIELD: Enrollment Status
    # Tracks whether student is currently active
    # Uses STATUS_CHOICES defined above
    # Default 'active' means new students are automatically active
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # ============================================================================
    # SYSTEM TIMESTAMPS
    # ============================================================================
    
    # FIELD: Enrollment Date
    # Automatically set when student record is created
    # auto_now_add=True means this is set once and never changes
    # Tracks when student first enrolled in the institution
    enrollment_date = models.DateField(auto_now_add=True)
    
    # ============================================================================
    # MODEL CONFIGURATION
    # ============================================================================
    
    class Meta:
        """
        META CLASS: Additional configuration options for the Student model
        
        CONFIGURATION EXPLAINED:
        
        db_table: Specifies custom table name 'student_student'
        - Default would be 'student_student' anyway, but explicitly defined
        - Helps with database migrations and backward compatibility
        
        verbose_name: Singular name for the model in Django admin
        - Shows "Student" instead of default "Student" (same in this case)
        - Used in form labels and admin interface
        
        verbose_name_plural: Plural name for the model in Django admin
        - Shows "Students" instead of default "Students" (same in this case) 
        - Used in admin interface list views
        
        ordering: Default sort order for Student queries
        - ['student_id'] means sort by student ID in ascending order
        - Ensures consistent ordering in lists and admin interface
        - Makes it easier to find specific students
        """
        db_table = 'student_student'
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        ordering = ['student_id']
    
    def __str__(self):
        """
        WHAT THIS METHOD DOES:
        Defines how Student objects are displayed as text throughout the system.
        
        FORMAT:
        "StudentID - Full Name"
        
        EXAMPLES:
        "ST001 - John Smith"
        "2024CS001 - Maria Garcia"  
        "STU123 - Ahmed Hassan"
        
        WHY THIS FORMAT:
        - Student ID provides unique identification
        - Full name provides human-readable identification
        - Combination ensures clarity in dropdowns, lists, and admin interface
        
        TECHNICAL DETAILS:
        - user.get_full_name() returns first_name + last_name from User model
        - If no full name is set, get_full_name() returns the username
        - This method is called automatically when Student objects are printed
        """
        return f"{self.student_id} - {self.user.get_full_name()}"
