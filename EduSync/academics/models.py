# ================================================================================
# ACADEMICS APP - MODELS.PY
# ================================================================================
# This file defines the core academic data structures for EduSync including:
# - Courses and academic programs
# - Branches (subject specializations)  
# - Student grades and assessments
# - Attendance tracking and sheets
# - Academic calendar and events
# - Event type and color management
#
# ACADEMIC SYSTEM OVERVIEW:
# EduSync organizes education through a hierarchical structure:
# Institution → Department → Branch → Course → Students/Teachers
# 
# Each institution can have multiple departments (Engineering, Science, etc.)
# Each department can have multiple branches (Computer Science, Electronics, etc.)
# Each branch can offer multiple courses (Data Structures, Algorithms, etc.)
# Students enroll in courses and receive grades for their performance.
#
# KEY RELATIONSHIPS & DATA FLOW:
# 1. Courses are offered by institutions and taught by teachers
# 2. Students enroll in courses and receive grades for performance
# 3. Attendance is tracked per student per teacher per department
# 4. Academic calendars organize semester schedules and events
# 5. Event types define different kinds of academic activities
# ================================================================================

# Import Django's database models and settings
from django.db import models
from django.conf import settings
# Import related models from other apps  
from teacher.models import Teacher
from institution.models import Institution


class Branch(models.Model):
    """
    WHAT THIS MODEL REPRESENTS:
    Academic branches are subject specializations within departments.
    They represent specific fields of study or academic disciplines.
    
    EXAMPLES OF BRANCHES:
    - Engineering Department: Computer Science, Electronics, Mechanical
    - Science Department: Physics, Chemistry, Biology, Mathematics  
    - Arts Department: English Literature, History, Philosophy
    - Business Department: Finance, Marketing, Human Resources
    
    PURPOSE:
    - Organize courses by academic specialization
    - Help students choose their field of study
    - Enable department-wise and branch-wise reporting
    - Support academic planning and resource allocation
    
    RELATIONSHIPS:
    - Branch belongs to one Institution (required)
    - Branch may belong to one Department (optional)
    - Multiple Courses can be offered within a Branch
    - Students can specialize in a Branch
    - Teachers can be assigned to teach Branch subjects
    """
    
    # FIELD: Institution Ownership
    # ForeignKey links branch to its parent institution
    # CASCADE means deleting institution also deletes all its branches
    # Required field - every branch must belong to an institution
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)
    
    # FIELD: Department Assignment
    # ForeignKey links branch to its parent department
    # SET_NULL preserves branch if department is deleted (allows reorganization)
    # Optional field - branches may exist independently of departments
    department = models.ForeignKey('institution.Department', on_delete=models.SET_NULL, null=True, blank=True)
    
    # FIELD: Branch Name
    # Human-readable name for the academic branch
    # Examples: "Computer Science", "Mechanical Engineering", "English Literature"
    # Required field with 200 character limit for detailed names
    name = models.CharField(max_length=200)
    
    # FIELD: Branch Description
    # Detailed description of the branch's focus and curriculum
    # Optional field for providing additional context about the specialization
    # TextField allows for comprehensive descriptions and course outlines
    description = models.TextField(blank=True, null=True)
    
    # FIELD: Creation Timestamp
    # Automatically set when branch record is created
    # auto_now_add=True means this is set once and never changes
    # Useful for tracking when branches were established
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """
        STRING REPRESENTATION:
        Returns the branch name for display in admin interface and forms.
        Simple and clear identification for users.
        
        EXAMPLE OUTPUT: "Computer Science"
        """
        return self.name


class Course(models.Model):
    """
    WHAT THIS MODEL REPRESENTS:
    Courses are specific academic subjects or classes offered by the institution.
    They represent individual learning units within academic programs.
    
    EXAMPLES OF COURSES:
    - "CS101 - Introduction to Programming"
    - "MATH201 - Calculus II"  
    - "ENG301 - Advanced Database Systems"
    - "BUS450 - Strategic Management"
    
    PURPOSE:
    - Define specific subjects students can take
    - Track course enrollment and completion
    - Assign teachers to specific courses
    - Calculate academic credits and fees
    - Support transcript and degree planning
    
    RELATIONSHIPS:
    - Course belongs to one Institution (required)
    - Course may belong to one Department (optional)
    - Course can have multiple Teachers (Many-to-Many)
    - Multiple Students can enroll in a Course
    - Each Course generates Grades for enrolled Students
    """
    
    # FIELD: Institution Ownership
    # ForeignKey links course to its parent institution
    # CASCADE means deleting institution also deletes all its courses
    # db_index=True creates database index for faster course queries
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, db_index=True)
    
    # FIELD: Course Code
    # Short alphanumeric identifier for the course
    # Examples: "CS101", "MATH201", "ENG301", "BUS450"
    # Used in transcripts, timetables, and official documentation
    # Combined with institution creates unique identifier
    code = models.CharField(max_length=20)
    
    # FIELD: Course Name
    # Full descriptive name of the course
    # Examples: "Introduction to Programming", "Advanced Database Systems"
    # Used in course catalogs and student enrollment interfaces
    name = models.CharField(max_length=200)
    
    # FIELD: Course Description
    # Detailed description of course content, objectives, and requirements
    # Optional field for providing comprehensive course information
    # Used in course catalogs and academic planning
    description = models.TextField(blank=True)
    
    # FIELD: Assigned Teachers
    # ManyToManyField allows multiple teachers to be assigned to one course
    # Supports team teaching and multiple section scenarios
    # blank=True makes this optional (courses can exist without assigned teachers)
    teachers = models.ManyToManyField(Teacher, blank=True)
    
    # FIELD: Credit Hours
    # Number of academic credits awarded for completing this course
    # Default 3 credits is standard for most courses
    # Used for degree requirements and academic load calculations
    credits = models.IntegerField(default=3)
    
    # FIELD: Course Duration
    # Length of the course in months
    # Default 0 means duration is not specified
    # PositiveIntegerField ensures only positive values
    # Useful for planning and scheduling
    duration_months = models.PositiveIntegerField(default=0)
    
    # FIELD: Department Association
    # Links course to academic department for organization
    # SET_NULL preserves course if department is deleted
    # Optional field - courses may span multiple departments
    department = models.ForeignKey('institution.Department', on_delete=models.SET_NULL, null=True, blank=True)
    
    # FIELD: Tuition Fee
    # Cost for enrolling in this course
    # DecimalField for precise financial calculations
    # max_digits=10, decimal_places=2 allows up to 99,999,999.99
    # Default 0.00 for free courses or when fees are not yet determined
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # FIELD: Creation Timestamp
    # Automatically set when course record is created
    # Useful for tracking when courses were added to the system
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """
        META CLASS CONFIGURATION:
        
        unique_together: Ensures combination of institution and course code is unique
        - Prevents duplicate course codes within the same institution  
        - Allows same course code across different institutions
        - Example: Both Institution A and B can have "CS101" but A can't have two "CS101" courses
        """
        unique_together = ('institution', 'code')

    def __str__(self):
        """
        STRING REPRESENTATION:
        Returns formatted course identifier combining code and name.
        
        FORMAT: "CODE - NAME"
        EXAMPLES:
        - "CS101 - Introduction to Programming"
        - "MATH201 - Calculus II"
        """
        return f"{self.code} - {self.name}"


class Grade(models.Model):
    """
    WHAT THIS MODEL REPRESENTS:
    Grades represent student performance assessments in specific courses.
    They connect students to courses with their earned grades and marks.
    
    PURPOSE:
    - Record student performance in courses
    - Calculate GPAs and academic standing
    - Generate transcripts and progress reports
    - Support academic analytics and reporting
    - Enable promotion and graduation decisions
    
    GRADING SYSTEM:
    This system uses traditional letter grades (A, B, C, D, F) where:
    - A: Excellent (90-100%)
    - B: Good (80-89%)  
    - C: Satisfactory (70-79%)
    - D: Pass (60-69%)
    - F: Fail (Below 60%)
    
    RELATIONSHIPS:
    - Each Grade belongs to one Student (required)
    - Each Grade belongs to one Course (required)
    - One Student can have multiple Grades (different courses)
    - One Course can have multiple Grades (different students)
    """
    
    # GRADE CHOICES: Predefined letter grade options
    # Ensures consistent grading across the system
    GRADE_CHOICES = [
        ('A', 'A'),  # Excellent performance
        ('B', 'B'),  # Good performance
        ('C', 'C'),  # Satisfactory performance
        ('D', 'D'),  # Minimum passing performance
        ('F', 'F'),  # Failing performance
    ]

    # FIELD: Student Assignment
    # ForeignKey links grade to the student who earned it
    # CASCADE means deleting student also deletes all their grades
    # Required field - every grade must belong to a student
    student = models.ForeignKey('student.Student', on_delete=models.CASCADE)
    
    # FIELD: Course Assignment
    # ForeignKey links grade to the course being assessed
    # CASCADE means deleting course also deletes all grades for that course
    # Required field - every grade must be for a specific course
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    
    # FIELD: Letter Grade
    # Uses predefined choices to ensure consistency
    # Single character field for traditional A-F grading
    # Required field - every grade record must have a letter grade
    grade = models.CharField(max_length=1, choices=GRADE_CHOICES)
    
    # FIELD: Numerical Marks
    # The numerical score that corresponds to the letter grade
    # FloatField allows decimal values (e.g., 87.5, 92.3)
    # Used for precise GPA calculations and detailed reporting
    marks = models.FloatField()
    
    # FIELD: Assignment Date
    # Automatically set when grade record is created
    # auto_now_add=True means this timestamp never changes
    # Useful for tracking when grades were entered/finalized
    date_assigned = models.DateTimeField(auto_now_add=True)

    class Meta:
        """
        META CLASS CONFIGURATION:
        
        unique_together: Ensures one grade per student per course
        - Prevents duplicate grade entries for the same student-course combination
        - If grade needs updating, existing record should be modified
        - Maintains data integrity for transcript generation
        """
        unique_together = ('student', 'course')

    def __str__(self):
        """
        STRING REPRESENTATION:
        Returns comprehensive grade information for display and debugging.
        
        FORMAT: "STUDENT - COURSE : GRADE"
        EXAMPLES:
        - "ST001 - John Smith - CS101 - Introduction to Programming : A"
        - "ST002 - Mary Johnson - MATH201 - Calculus II : B"
        """
        return f"{self.student} - {self.course} : {self.grade}"


class AttendanceSheet(models.Model):
    """
    WHAT THIS MODEL REPRESENTS:
    AttendanceSheet is a container for tracking attendance during a specific period.
    It represents a teacher's attendance record for a department over a date range.
    
    PURPOSE:
    - Generate attendance reports for specific periods
    - Track teaching assignments and responsibilities  
    - Enable bulk attendance recording and analysis
    - Support academic compliance and reporting
    - Provide data for teacher performance evaluation
    
    WORKFLOW:
    1. Teacher creates attendance sheet for their department/subject
    2. Sheet covers specific date range (e.g., monthly, semester)
    3. Individual student attendance records link to this sheet
    4. Sheet can be shared with students for transparency
    5. Used for generating attendance reports and analytics
    
    RELATIONSHIPS:
    - AttendanceSheet belongs to one Teacher (required)
    - AttendanceSheet belongs to one Department (required)  
    - AttendanceSheet contains multiple Attendance records
    - Each sheet covers a specific date range
    """
    
    # FIELD: Teacher Assignment
    # ForeignKey links attendance sheet to the teacher who manages it
    # CASCADE means deleting teacher also deletes their attendance sheets
    # Required field - every sheet must have a responsible teacher
    teacher = models.ForeignKey('teacher.Teacher', on_delete=models.CASCADE)
    
    # FIELD: Department Assignment
    # ForeignKey links sheet to the academic department
    # CASCADE means deleting department also deletes its attendance sheets
    # Required field - sheets are organized by department
    department = models.ForeignKey('institution.Department', on_delete=models.CASCADE)
    
    # FIELD: Period Start Date
    # First date covered by this attendance sheet
    # Required field - defines the beginning of the tracking period
    date_from = models.DateField()
    
    # FIELD: Period End Date
    # Last date covered by this attendance sheet
    # Required field - defines the end of the tracking period
    date_to = models.DateField()
    
    # FIELD: Total Lecture Count
    # Total number of lectures conducted during the period
    # PositiveIntegerField ensures only positive values
    # Used as denominator for attendance percentage calculations
    total_lectures = models.PositiveIntegerField()
    
    # FIELD: Creation Timestamp
    # When the attendance sheet was first created
    # auto_now_add=True sets this once and never changes
    # Useful for tracking when sheets were generated
    created_at = models.DateTimeField(auto_now_add=True)
    
    # FIELD: Last Update Timestamp
    # When the attendance sheet was last modified
    # auto_now=True updates this every time the record is saved
    # Useful for tracking ongoing attendance updates
    updated_at = models.DateTimeField(auto_now=True)
    
    # FIELD: Student Sharing Status
    # Boolean flag indicating if sheet is visible to students
    # Default False means sheets are private to teachers/admin by default
    # When True, students can view their attendance records
    shared_with_students = models.BooleanField(default=False)

    class Meta:
        """
        META CLASS CONFIGURATION:
        
        unique_together: Prevents duplicate sheets for same teacher/dept/period
        - Ensures one sheet per teacher per department per time period
        - Prevents conflicting attendance records
        - Maintains data integrity for reporting
        
        ordering: Default sort order for sheet queries
        - ['-created_at'] sorts by creation date with newest first
        - Helpful for displaying recent sheets first in interfaces
        """
        unique_together = ('teacher', 'department', 'date_from', 'date_to')
        ordering = ['-created_at']

    def __str__(self):
        """
        STRING REPRESENTATION:
        Returns comprehensive sheet identification for display.
        
        FORMAT: "TEACHER - DEPARTMENT (START_DATE to END_DATE)"
        EXAMPLES:
        - "EMP001 - Dr. Smith - Computer Science (2024-01-01 to 2024-01-31)"
        - "EMP002 - Prof. Johnson - Mathematics (2024-02-01 to 2024-02-28)"
        """
        return f"{self.teacher} - {self.department.name} ({self.date_from} to {self.date_to})"


class Attendance(models.Model):
    """
    WHAT THIS MODEL REPRESENTS:
    Individual attendance record for a specific student within an attendance sheet.
    Tracks how many lectures a student attended out of the total conducted.
    
    PURPOSE:
    - Record individual student attendance data
    - Calculate attendance percentages automatically
    - Support attendance-based academic decisions
    - Enable student progress monitoring
    - Generate attendance reports and analytics
    
    ATTENDANCE CALCULATION:
    Percentage = (lectures_attended / total_lectures) × 100
    
    ACADEMIC IMPORTANCE:
    - Many institutions require minimum attendance (e.g., 75%) for exam eligibility
    - Attendance affects grades and academic standing
    - Used for identifying at-risk students
    - Required for regulatory compliance and accreditation
    
    RELATIONSHIPS:
    - Attendance belongs to one AttendanceSheet (required)
    - Attendance belongs to one Student (required)
    - Multiple Attendance records per student (different sheets/periods)
    """
    
    # FIELD: Attendance Sheet Reference
    # ForeignKey links to the parent attendance sheet
    # CASCADE means deleting sheet also deletes all its attendance records
    # related_name='attendance_records' allows reverse lookup from sheet
    sheet = models.ForeignKey(AttendanceSheet, on_delete=models.CASCADE, related_name='attendance_records')
    
    # FIELD: Student Reference
    # ForeignKey links to the student being tracked
    # CASCADE means deleting student also deletes all their attendance records  
    # related_name='attendance_records' allows reverse lookup from student
    student = models.ForeignKey('student.Student', on_delete=models.CASCADE, related_name='attendance_records')
    
    # FIELD: Lectures Attended
    # Number of lectures the student actually attended
    # PositiveIntegerField ensures only positive values (including 0)
    # Default 0 for new records where attendance hasn't been marked yet
    lectures_attended = models.PositiveIntegerField(default=0)
    
    # FIELD: Total Lectures
    # Total number of lectures conducted (should match sheet's total_lectures)
    # PositiveIntegerField ensures only positive values
    # Required field - used as denominator for percentage calculation
    
    total_lectures = models.PositiveIntegerField()
    class Meta:
        """
        META CLASS CONFIGURATION:
        
        unique_together: Ensures one attendance record per student per sheet
        - Prevents duplicate attendance records for same student in same period
        - Maintains data integrity for attendance calculations
        - Each student should have exactly one record per attendance sheet
        
        ordering: Default sort order for attendance queries
        - ['student__student_id'] sorts by student ID in ascending order
        - Provides consistent ordering for attendance reports and lists
        - Makes it easier to find specific student records
        """
        unique_together = ('sheet', 'student')
        ordering = ['student__student_id']

    def __str__(self):
        """
        STRING REPRESENTATION:
        Returns attendance summary showing attended vs total lectures.
        
        FORMAT: "STUDENT - ATTENDED/TOTAL"
        EXAMPLES:
        - "ST001 - John Smith - 18/20"
        - "ST002 - Mary Johnson - 15/20"
        
        This format quickly shows attendance status for easy review.
        """
        return f"{self.student} - {self.lectures_attended}/{self.total_lectures}"

    @property
    def attendance_percentage(self):
        """
        CALCULATED PROPERTY: Automatic attendance percentage calculation
        
        WHAT THIS PROPERTY DOES:
        Calculates and returns the student's attendance percentage as a decimal.
        
        CALCULATION LOGIC:
        1. Check if total_lectures is 0 to avoid division by zero
        2. If 0 lectures, return 0% (no attendance data yet)
        3. Otherwise: (lectures_attended ÷ total_lectures) × 100
        4. Round result to 2 decimal places for display
        
        EXAMPLES:
        - 18 attended out of 20 total = 90.00%
        - 15 attended out of 20 total = 75.00%
        - 0 attended out of 0 total = 0% (safe fallback)
        
        USAGE IN TEMPLATES:
        {{ attendance.attendance_percentage }}% displays calculated percentage
        
        ACADEMIC SIGNIFICANCE:
        - Most institutions require 75% minimum attendance
        - Used for exam eligibility decisions
        - Affects academic standing and progress
        - Required for regulatory compliance
        """
        # Safety check: prevent division by zero
        if self.total_lectures == 0:
            return 0
        
        # Calculate percentage: (attended ÷ total) × 100
        # Round to 2 decimal places for clean display
        return round((self.lectures_attended / self.total_lectures) * 100, 2)


class AcademicCalendar(models.Model):
    """
    WHAT THIS MODEL REPRESENTS:
    AcademicCalendar represents a semester-wise academic schedule container.
    It groups calendar events (holidays, exams, breaks) for a specific academic period.
    
    PURPOSE:
    - Organize academic events by semester and year
    - Enable department-specific or institution-wide calendars
    - Control visibility of calendars to students and teachers
    - Support academic planning and scheduling
    - Provide structure for event management
    
    CALENDAR HIERARCHY:
    Institution → Department → AcademicCalendar → CalendarEvent
    
    VISIBILITY CONTROL:
    Admins can control who sees each calendar:
    - shared_with_students: Students can view (but not edit) calendar
    - shared_with_teachers: Teachers can view (but not edit) calendar
    - Default: Only admins can see and edit calendars
    
    MULTI-TENANCY SUPPORT:
    - Institution-wide calendars: department = null (affects all departments)
    - Department-specific calendars: department = specific department
    - Enables fine-grained academic scheduling control
    
    RELATIONSHIPS:
    - AcademicCalendar may belong to one Department (optional)
    - AcademicCalendar belongs to one Creator (User who made it)
    - AcademicCalendar contains multiple CalendarEvents
    """
    
    # FIELD: Semester Name
    # Name of the academic semester or term
    # Examples: "Fall 2024", "Spring 2025", "Summer Session", "First Semester"
    # CharField with 30 characters handles various naming conventions
    semester = models.CharField(max_length=30)
    
    # FIELD: Academic Year
    # Year or year range for the academic period  
    # Examples: "2024", "2024-2025", "AY 2024-25"
    # CharField with 20 characters handles different year formats
    year = models.CharField(max_length=20)

    # FIELD: Target Department (Optional)
    # Optional link to specific department for department-specific calendars
    # SET_NULL preserves calendar if department is deleted/restructured
    # null=True, blank=True makes calendar institution-wide when not set
    # related_name='calendars' allows reverse lookup from department
    department = models.ForeignKey(
        'institution.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='calendars'
    )

    # FIELD: Calendar Creator
    # User who created this academic calendar (admin or authorized user)
    # PROTECT prevents deletion if creator user account is deleted
    # related_name='academic_calendars' allows reverse lookup from user
    # Links to Django's User model via settings.AUTH_USER_MODEL
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='academic_calendars'
    )

    # FIELD: Student Visibility Flag
    # Controls whether students can view this calendar
    # Default False = calendar is private to admins/staff
    # True = students can see events in this calendar
    # Does NOT grant editing permissions (students are always read-only)
    shared_with_students = models.BooleanField(default=False)
    
    # FIELD: Institution Reference
    # Links the calendar to a specific institution for multi-tenancy.
    # CASCADE means deleting institution also deletes all its calendars.
    # Required for clear data ownership and access control.
    institution = models.ForeignKey(
        'institution.Institution',
        on_delete=models.CASCADE,
        related_name='academic_calendars_new',
        null=True,
        blank=True
    )

    # FIELD: Teacher Visibility Flag  
    # Controls whether teachers can view this calendar
    # Default False = calendar is private to admins
    # True = teachers can see events in this calendar
    # Does NOT grant editing permissions (teachers are read-only unless admin)
    shared_with_teachers = models.BooleanField(default=False)

    # FIELD: Creation Timestamp
    # When the calendar was first created
    # auto_now_add=True sets this once and never changes
    # Useful for tracking calendar creation history
    created_at = models.DateTimeField(auto_now_add=True)
    
    # FIELD: Last Update Timestamp
    # When the calendar was last modified
    # auto_now=True updates this every time the record is saved
    # Useful for tracking recent calendar changes
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """
        META CLASS CONFIGURATION:
        
        db_table: Custom database table name 'academic_calendar'
        - Overrides default 'academics_academiccalendar'
        - Provides cleaner, shorter table name
        - Consistent with database naming conventions
        
        ordering: Default sort order for calendar queries
        - ['-created_at'] sorts by creation date with newest first
        - Helpful for displaying recent calendars first
        - Ensures consistent ordering in admin interface
        """
        db_table = 'academic_calendar'
        ordering = ['-created_at']

    def __str__(self):
        """
        STRING REPRESENTATION:
        Returns calendar identifier combining semester and year.
        
        FORMAT: "SEMESTER (YEAR)"
        EXAMPLES:
        - "Fall 2024 (2024-2025)"
        - "Spring Semester (2025)"
        - "Summer Session (2024)"
        
        Clear identification for admin interface and dropdowns.
        """
        return f"{self.semester} ({self.year})"


class CalendarEvent(models.Model):
    """
    WHAT THIS MODEL REPRESENTS:
    Individual events within an academic calendar representing specific dates
    and activities in the academic schedule (holidays, exams, classes, etc.).
    
    PURPOSE:
    - Define specific academic activities and their dates
    - Categorize events by type for easy filtering and color coding
    - Provide detailed information about academic schedule items
    - Support calendar visualization and student/teacher notifications
    - Enable academic planning and resource allocation
    
    EVENT TYPES EXPLAINED:
    - Regular Teaching: Normal class sessions and lectures
    - Test: Exams, quizzes, assessments, evaluations
    - Reading Holiday: Study periods before exams (no classes)
    - Public Holiday: Government holidays (offices closed)
    - Semester Break: Vacation periods between semesters
    - Festival Holiday: Religious or cultural celebrations
    - Project / Practical Evaluation: Lab work, project presentations
    
    COLOR CODING SYSTEM:
    Each event type has an associated color for visual calendar display:
    - Colors help users quickly identify event types
    - Default colors provided but customizable via EventTypeColor model
    - Supports calendar UI and student/teacher dashboards
    
    RELATIONSHIPS:
    - CalendarEvent belongs to one AcademicCalendar (required)
    - Multiple CalendarEvents per AcademicCalendar
    - EventTypeColor model can override default colors
    """
    
    # EVENT TYPE CHOICES: Predefined categories for academic events
    # These represent different kinds of activities in academic calendar
    EVENT_TYPES = [
        ('Regular Teaching', 'Regular Teaching'),          # Normal class sessions
        ('Test', 'Test'),                                 # Exams and assessments
        ('Reading Holiday', 'Reading Holiday'),           # Study periods (no classes)
        ('Public Holiday', 'Public Holiday'),             # Government holidays
        ('Semester Break', 'Semester Break'),             # Vacation periods
        ('Festival Holiday', 'Festival Holiday'),         # Cultural/religious holidays
        ('Project / Practical Evaluation', 'Project / Practical Evaluation'), # Lab/project work
    ]

    # DEFAULT COLOR PALETTE: Built-in colors for each event type
    # These colors are used if no custom colors are set in EventTypeColor model
    # Colors use hex format for web compatibility (#RRGGBB)
    DEFAULT_TYPE_COLORS = {
        'Regular Teaching': '#3B82F6',                    # Blue - calm, productive
        'Test': '#EF4444',                               # Red - attention, important
        'Reading Holiday': '#F59E0B',                    # Amber - caution, preparation
        'Public Holiday': '#10B981',                     # Green - rest, celebration
        'Semester Break': '#64748B',                     # Gray - neutral, break
        'Festival Holiday': '#F97316',                   # Orange - festive, cultural
        'Project / Practical Evaluation': '#6366F1',     # Indigo - focus, assessment
    }

    # FIELD: Parent Calendar
    # ForeignKey links event to its academic calendar container
    # CASCADE means deleting calendar also deletes all its events
    # related_name='events' allows reverse lookup from calendar
    # Required field - every event must belong to a calendar
    calendar = models.ForeignKey(
        AcademicCalendar,
        on_delete=models.CASCADE,
        related_name='events'
    )
    
    # FIELD: Event Date
    # The specific date when this event occurs
    # DateField for calendar integration and date-based queries
    # Required field - every event must have a specific date
    date = models.DateField()
    
    # FIELD: Event Title
    # Short descriptive name for the event
    # Examples: "Final Exams Begin", "Independence Day", "Spring Break Starts"
    # 150 characters allows descriptive but concise titles
    title = models.CharField(max_length=150)
    
    # FIELD: Event Type
    # Categorizes the event using predefined choices
    # Uses EVENT_TYPES defined above for consistency
    # 50 characters handles longest type name
    # Required field for proper categorization and color coding
    type = models.CharField(max_length=50, choices=EVENT_TYPES)
    
    # FIELD: Event Description
    # Detailed information about the event
    # Optional field for providing additional context
    # TextField allows comprehensive event details
    # Examples: exam schedules, holiday explanations, break activities
    description = models.TextField(blank=True)
    
    # FIELD: Display Color
    # Hex color code for calendar visualization
    # Default '#2563EB' (blue) for general events
    # Can be overridden by event type defaults or EventTypeColor settings
    # 20 characters handles hex colors and color names
    color_code = models.CharField(max_length=20, default='#2563EB')
    
    # FIELD: Creation Timestamp
    # When the event was first created
    # auto_now_add=True sets this once and never changes
    # Useful for tracking event creation history
    created_at = models.DateTimeField(auto_now_add=True)
    
    # FIELD: Last Update Timestamp
    # When the event was last modified
    # auto_now=True updates this every time the record is saved
    # Useful for tracking recent event changes
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """
        META CLASS CONFIGURATION:
        
        db_table: Custom database table name 'calendar_events'
        - Overrides default 'academics_calendarevent'
        - Provides cleaner, more descriptive table name
        - Consistent with database naming conventions
        
        ordering: Default sort order for event queries
        - ['date', 'id'] sorts by event date first, then by ID
        - Ensures chronological ordering for calendar display
        - ID as secondary sort handles multiple events on same date
        """
        db_table = 'calendar_events'
        ordering = ['date', 'id']

    def __str__(self):
        """
        STRING REPRESENTATION:
        Returns event identifier combining date and title.
        
        FORMAT: "DATE - TITLE"
        EXAMPLES:
        - "2024-12-25 - Christmas Holiday"
        - "2024-01-15 - Final Exams Begin"
        - "2024-03-01 - Spring Break Starts"
        
        Clear chronological identification for admin interface.
        """
        return f"{self.date} - {self.title}"

    @classmethod
    def get_type_color_mapping(cls):
        """
        CLASS METHOD: Get complete event type to color mapping
        
        WHAT THIS METHOD DOES:
        Creates a dictionary mapping each event type to its display color.
        Combines default colors with any database overrides from EventTypeColor.
        
        PRIORITY SYSTEM:
        1. Start with DEFAULT_TYPE_COLORS (built-in defaults)
        2. Override with any colors set in EventTypeColor model (admin customizations)
        3. Return complete mapping for all event types
        
        ERROR HANDLING:
        - Uses try/except to handle database access errors
        - Safe to call during migrations when tables might not exist yet
        - Falls back to default colors if database access fails
        - Ensures method always returns usable color mapping
        
        USAGE:
        colors = CalendarEvent.get_type_color_mapping()
        color = colors['Test']  # Gets color for Test events
        
        RETURNS:
        Dictionary: {'event_type': '#color_code', ...}
        
        EXAMPLES:
        {
            'Regular Teaching': '#3B82F6',
            'Test': '#FF0000',  # Custom override from EventTypeColor
            'Public Holiday': '#10B981',
            ...
        }
        """
        # Start with built-in default colors as base mapping
        mapping = dict(cls.DEFAULT_TYPE_COLORS)
        
        try:
            # Try to get custom color overrides from database
            # EventTypeColor may not exist during migrations, so guard with try/except
            for override in EventTypeColor.objects.all():
                # Override default color with admin-configured color
                mapping[override.event_type] = override.color_code
        except Exception:
            # Any database access error → return static defaults
            # This handles migration scenarios and database connectivity issues
            pass
        
        return mapping

    @classmethod
    def color_for_type(cls, ev_type):
        """
        CLASS METHOD: Get color for a specific event type
        
        WHAT THIS METHOD DOES:
        Convenient method to get the color for just one event type.
        Uses get_type_color_mapping() internally for consistency.
        
        FALLBACK SYSTEM:
        1. Try to get color from complete mapping (includes overrides)
        2. Fall back to DEFAULT_TYPE_COLORS if type not found
        3. Final fallback to '#2563EB' (blue) if all else fails
        
        PARAMETERS:
        ev_type (str): Event type name (e.g., 'Test', 'Public Holiday')
        
        RETURNS:
        str: Hex color code (e.g., '#EF4444')
        
        USAGE EXAMPLES:
        color = CalendarEvent.color_for_type('Test')           # Returns red color
        color = CalendarEvent.color_for_type('Unknown Type')   # Returns fallback blue
        
        TEMPLATE USAGE:
        Can be used in templates for dynamic color assignment
        """
        # Get complete type-to-color mapping (includes overrides)
        complete_mapping = cls.get_type_color_mapping()
        
        # Try to find color in complete mapping, fall back to default, then final fallback
        return complete_mapping.get(
            ev_type,                                    # Try complete mapping first
            cls.DEFAULT_TYPE_COLORS.get(ev_type, '#2563EB')  # Fall back to default, then blue
        )


class EventTypeColor(models.Model):
    """
    WHAT THIS MODEL REPRESENTS:
    Administrative overrides for event type colors in calendar displays.
    Allows admins to customize the color scheme for different event types.
    
    PURPOSE:
    - Enable custom color schemes for institutions
    - Override default colors with brand/theme colors
    - Provide admin control over calendar visual appearance
    - Support accessibility and user preference requirements
    - Maintain color consistency across calendar views
    
    HOW IT WORKS:
    1. Default colors are defined in CalendarEvent.DEFAULT_TYPE_COLORS
    2. Admins can create EventTypeColor records to override defaults
    3. CalendarEvent.get_type_color_mapping() prioritizes these overrides
    4. Calendar UI uses the resulting colors for display
    
    ADMINISTRATIVE CONTROL:
    - Only admins should be able to create/modify these records
    - Changes affect all calendar displays institution-wide
    - Provides centralized color theme management
    - Supports branding and visual consistency requirements
    
    RELATIONSHIPS:
    - EventTypeColor overrides CalendarEvent default colors
    - One EventTypeColor per event type (unique constraint)
    - Referenced by CalendarEvent color methods
    """
    
    # FIELD: Event Type Reference
    # Links to specific event type from CalendarEvent.EVENT_TYPES
    # Uses same choices to ensure consistency
    # unique=True ensures only one color override per event type
    # 50 characters matches CalendarEvent.type field length
    EVENT_TYPE_CHOICES = CalendarEvent.EVENT_TYPES
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES, unique=True)
    
    # FIELD: Override Color Code
    # Hex color code to use instead of the default color
    # Examples: '#FF5722', '#2196F3', '#4CAF50'
    # Default '#2563EB' (blue) for newly created overrides
    # 20 characters handles hex colors and extended color formats
    color_code = models.CharField(max_length=20, default='#2563EB')
    
    # FIELD: Last Update Timestamp
    # When this color override was last modified
    # auto_now=True updates this every time the record is saved
    # Useful for tracking color scheme changes and updates
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """
        META CLASS CONFIGURATION:
        
        db_table: Custom database table name 'event_type_colors'
        - Overrides default 'academics_eventtypecolor'
        - Provides cleaner, more descriptive table name
        - Consistent with other custom table names in project
        
        ordering: Default sort order for color override queries
        - ['event_type'] sorts alphabetically by event type name
        - Provides consistent ordering in admin interface
        - Makes it easier to find and manage color overrides
        """
        db_table = 'event_type_colors'
        ordering = ['event_type']

    def __str__(self):
        """
        STRING REPRESENTATION:
        Returns color override identification showing type and color.
        
        FORMAT: "EVENT_TYPE (COLOR_CODE)"
        EXAMPLES:
        - "Test (#FF0000)"
        - "Public Holiday (#00FF00)"
        - "Regular Teaching (#0000FF)"
        
        Clear identification for admin interface and debugging.
        Shows both what type is being overridden and what color it uses.
        """
        return f"{self.event_type} ({self.color_code})"
