# ================================================================================
# TEACHER APP - MODELS.PY
# ================================================================================
# This file defines the database structure for teacher/faculty management in EduSync.
# It contains the Teacher model which stores all information about teaching staff
# including employment details, academic qualifications, and institutional assignments.
#
# WHAT IS A TEACHER IN EDUSYNC?
# A teacher (also called faculty, instructor, or professor) is an employee who
# provides education and instruction to students. The Teacher model extends Django's
# User system to store employment-specific and academic information.
#
# KEY RELATIONSHIPS:
# - Teacher ←→ User (One-to-One): Each teacher has one login account
# - Teacher ←→ Institution (Many-to-One): Teachers work at one institution
# - Teacher ←→ Department (Many-to-One): Teachers are assigned to academic departments
# - Teacher ←→ Branch (Many-to-One): Teachers may specialize in specific branches
# - Teacher ←→ Course (Many-to-Many): Teachers can teach multiple courses (via academics app)
#
# EMPLOYMENT HIERARCHY:
# Institution → Department → Branch → Teacher → Subjects/Courses
# This hierarchy organizes teaching staff for administrative and academic purposes.
# ================================================================================

# Import Django's database models and User authentication system
from django.db import models
from django.contrib.auth.models import User
# Import Institution model to establish employment relationships
from institution.models import Institution


class Teacher(models.Model):
    """
    WHAT THIS MODEL REPRESENTS:
    The Teacher model stores comprehensive information about teaching staff employed
    by the educational institution. This includes employment terms, qualifications,
    contact information, and academic assignments.
    
    PURPOSE:
    - Manage teacher employment and HR records
    - Track qualifications and specializations
    - Organize teachers by departments and subjects
    - Support payroll and contract management
    - Enable academic scheduling and course assignments
    
    WHO HAS ACCESS:
    - Institution admins: Full access to all teacher data including salary
    - Department heads: Access to teachers in their department
    - Teachers: Access to their own profile information
    - HR staff: Access to employment and payroll information
    
    DATABASE TABLE NAME:
    This model will create a table named 'teacher_teacher' by default.
    """
    
    # CHOICE FIELDS: Predefined options for certain fields
    # These ensure data consistency and support HR reporting
    
    # Gender Options
    # Supports inclusive gender identification for HR records
    GENDER_CHOICES = [
        ('M', 'Male'),      # Male teachers
        ('F', 'Female'),    # Female teachers
        ('O', 'Other'),     # Non-binary, prefer not to say, etc.
    ]
    
    # Employment Contract Types
    # Defines different types of teaching positions and contracts
    CONTRACT_CHOICES = [
        ('Full-Time', 'Full-Time'),  # Permanent full-time employment
        ('Part-Time', 'Part-Time'),  # Regular part-time employment  
        ('Contract', 'Contract'),    # Fixed-term contract positions
        ('Guest', 'Guest'),          # Guest lecturers or visiting faculty
    ]
    
    # ============================================================================
    # AUTHENTICATION & INSTITUTIONAL RELATIONSHIPS
    # ============================================================================
    
    # FIELD: User Account Connection
    # OneToOneField links each teacher to exactly one Django User account
    # Provides login credentials, email, first_name, last_name from User model
    # on_delete=CASCADE means deleting User account also deletes Teacher record
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # FIELD: Institution Employment
    # ForeignKey links teacher to their employing institution
    # Enables multi-tenant system where each institution manages its own staff
    # on_delete=CASCADE means deleting Institution also deletes all its teachers
    # db_index=True creates database index for faster queries (important for staff lists)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, db_index=True)
    
    # ============================================================================
    # EMPLOYMENT IDENTIFICATION & ASSIGNMENT
    # ============================================================================
    
    # FIELD: Employee ID Number
    # Unique identifier for the teacher within the HR system
    # Examples: "EMP001", "T2024001", "FAC123456"
    # unique=True ensures no two teachers have the same ID globally across all institutions
    # Used for payroll, attendance tracking, and official documentation
    employee_id = models.CharField(max_length=20, unique=True)
    
    # FIELD: Department Assignment
    # Links teacher to their primary academic department
    # Examples: "Computer Science", "Mathematics", "English Literature"
    # SET_NULL preserves teacher record if department is deleted/restructured
    # db_index=True for fast department-wise teacher queries
    department = models.ForeignKey('institution.Department', on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    
    # FIELD: Branch/Subject Specialization
    # Links teacher to specific academic branch within their department
    # Examples: "Data Structures", "Calculus", "Modern Literature"
    # SET_NULL preserves teacher record if branch is deleted
    # Optional field as some teachers may teach across multiple branches
    branch = models.ForeignKey('academics.Branch', on_delete=models.SET_NULL, null=True, blank=True)
    
    # ============================================================================
    # ACADEMIC QUALIFICATIONS
    # ============================================================================
    
    # FIELD: Educational Qualification
    # Teacher's highest degree or professional qualification
    # Examples: "Ph.D. in Computer Science", "M.Tech Electronics", "MBA Finance"
    # CharField with 200 characters allows for detailed qualification descriptions
    # Required field - all teachers must have documented qualifications
    qualification = models.CharField(max_length=200)
    
    # ============================================================================
    # PERSONAL INFORMATION
    # ============================================================================
    
    # FIELD: Gender Identity
    # Uses predefined choices for HR reporting and diversity tracking
    # Default 'M' for backwards compatibility (can be changed during onboarding)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M')
    
    # FIELD: Date of Birth
    # Used for age verification, retirement planning, and HR demographics
    # Optional fields (null=True, blank=True) as this may be sensitive information
    # Important for calculating service periods and retirement benefits
    date_of_birth = models.DateField(null=True, blank=True)
    
    # FIELD: Employment Start Date
    # Automatically recorded when teacher record is created
    # auto_now_add=True sets this once when the record is first saved
    # Used for calculating tenure, promotions, and benefits eligibility
    hire_date = models.DateField(auto_now_add=True)
    
    # ============================================================================
    # CONTACT INFORMATION
    # ============================================================================
    
    # FIELD: Phone Number
    # Teacher's contact phone number for official communication
    # Optional field as email is primary communication method
    # Used for emergency contacts and urgent academic matters
    phone = models.CharField(max_length=15, blank=True)
    
    # FIELD: Residential Address
    # Teacher's home address for HR records and official correspondence
    # TextField allows for complete multi-line addresses
    # Optional but recommended for employment documentation
    address = models.TextField(blank=True)
    
    # ============================================================================
    # EMPLOYMENT TERMS & COMPENSATION
    # ============================================================================
    
    # FIELD: Salary Amount
    # Teacher's monthly or annual salary
    # DecimalField ensures precise financial calculations
    # max_digits=12 allows for large salary amounts (up to 999,999,999,999.99)
    # decimal_places=2 for currency precision (cents/paise)
    # Default 0.00 for new appointments pending salary determination
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # FIELD: Contract Type
    # Defines the nature of employment relationship
    # Uses CONTRACT_CHOICES defined above for consistency
    # Default 'Full-Time' assumes most teachers are full-time employees
    # Important for payroll processing and benefits calculation
    contract_type = models.CharField(max_length=20, choices=CONTRACT_CHOICES, default='Full-Time')
    
    # ============================================================================
    # PROFILE MEDIA
    # ============================================================================
    
    # FIELD: Profile Photo
    # Teacher's photograph for ID cards, website, and official documents
    # ImageField handles image upload and storage
    # upload_to='teachers/' organizes photos in media/teachers/ directory
    # Optional field (blank=True, null=True) as photos may not be immediately available
    photo = models.ImageField(upload_to='teachers/', blank=True, null=True)
    
    # ============================================================================
    # COMPUTED PROPERTIES (NOT DATABASE FIELDS)
    # ============================================================================
    
    @property
    def initials(self):
        """
        WHAT THIS PROPERTY DOES:
        Generates teacher's initials for display in UI elements like avatars,
        timetables, and compact lists where full names don't fit.
        
        LOGIC EXPLANATION:
        1. Get full name from User model (first_name + last_name)
        2. If full name exists: Take first letter of each word and capitalize
        3. If no full name: Use first 3 characters of username and capitalize
        
        EXAMPLES:
        - "John Smith" → "JS"
        - "Dr. Sarah Johnson" → "DSJ"  
        - "ahmed.hassan" (username only) → "AHM"
        - "mary" (username only) → "MAR"
        
        USAGE IN TEMPLATES:
        {{ teacher.initials }} displays the calculated initials
        
        WHY USE @property:
        - Not stored in database (calculated each time)
        - Accessed like a field: teacher.initials
        - Always up-to-date if name changes
        - Saves database storage space
        """
        # Get the full name from the associated User model
        full_name = self.user.get_full_name()
        
        # If no full name is set, use username as fallback
        if not full_name:
            # Take first 3 characters of username and convert to uppercase
            return self.user.username[:3].upper()
        
        # Split full name into individual words and take first letter of each
        # List comprehension: [n[0].upper() for n in full_name.split() if n]
        # - full_name.split(): Split name into words ["John", "Smith"] 
        # - if n: Skip empty strings (handles extra spaces)
        # - n[0]: Take first character of each word
        # - .upper(): Convert to uppercase
        # - "".join(): Combine all initials into one string
        return "".join([n[0].upper() for n in full_name.split() if n])

    def __str__(self):
        """
        WHAT THIS METHOD DOES:
        Defines how Teacher objects are displayed as text throughout the system.
        
        FORMAT:
        "EmployeeID - Username"
        
        EXAMPLES:
        "EMP001 - john.smith"
        "T2024001 - dr.sarah"  
        "FAC123 - ahmed.hassan"
        
        WHY THIS FORMAT:
        - Employee ID provides official identification
        - Username provides login identification
        - Combination ensures clarity in admin interface and dropdowns
        
        TECHNICAL DETAILS:
        - self.user refers to the associated User model
        - When User object is converted to string, it returns the username
        - This method is called automatically when Teacher objects are printed
        - Used in Django admin, form dropdowns, and debugging output
        """
        return f"{self.employee_id} - {self.user}"
