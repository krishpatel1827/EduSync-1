# ================================================================================
# GENERATOR APP - MODELS.PY
# ================================================================================
# This file defines the database structure for timetable generation and management.
# It contains models that handle institutional scheduling, room allocation,
# faculty assignments, and automated timetable creation.
#
# WHAT IS THE GENERATOR APP?
# The Generator app is responsible for creating and managing class timetables.
# It allows institutions to automatically generate weekly schedules that assign:
# - Teachers to time slots
# - Subjects to specific periods
# - Rooms to classes
# - Students (divisions) to schedules
#
# TIMETABLE SYSTEM OVERVIEW:
# Institution creates Timetable → Defines TimeSlots → Assigns Rooms/Divisions →
# Creates TimetableEntries → Generates printable schedule
#
# KEY COMPONENTS:
# 1. Timetable: Container for an entire weekly schedule
# 2. TimeSlot: Individual lectures/periods within a day
# 3. Room: Physical classroom locations
# 4. Division: Student groups/classes
# 5. TimetableEntry: Specific assignment of teacher+subject+room+time+division
#
# SCHEDULING CONSTRAINTS:
# - No double booking: One room/faculty/division per time slot
# - Time conflict prevention: Built-in unique constraints
# - Flexible scheduling: Support for breaks and variable periods
# - Multi-institutional support: Separate timetables per institution
# ================================================================================

# Import Django's database models
from django.db import models
# Import related models from other apps for relationships
from academics.models import Course
from teacher.models import Teacher
from institution.models import Institution


class Timetable(models.Model):
    """
    WHAT THIS MODEL REPRESENTS:
    A Timetable is the master container for an entire weekly schedule.
    It defines the structure, branding, and organization of class schedules.
    
    PURPOSE:
    - Create institutional weekly schedules
    - Organize different timetables by department/course/branch
    - Support multiple versions (draft, published, archived)
    - Enable custom branding and formatting for printed schedules
    - Provide version control for schedule changes
    
    TIMETABLE LIFECYCLE:
    1. Create Draft: Initial timetable with basic information
    2. Configure: Set up time slots, rooms, divisions
    3. Generate: Auto-assign or manually create entries
    4. Review: Check for conflicts and optimize
    5. Publish: Make active for students and teachers
    6. Archive: Preserve for historical records
    
    MULTI-LEVEL ORGANIZATION:
    - Institution-wide timetables: All departments
    - Department-specific timetables: One department
    - Course-specific timetables: Specific program
    - Branch-specific timetables: Subject specialization
    
    RELATIONSHIPS:
    - Timetable belongs to Institution, Department, Course, Branch (all optional)
    - Timetable created by User (admin/scheduler)
    - Timetable contains multiple TimeSlots, Divisions, TimetableEntries
    """
    
    # ============================================================================
    # ORGANIZATIONAL RELATIONSHIPS
    # ============================================================================
    
    # FIELD: Institution Assignment
    # Links timetable to parent institution for multi-tenant support
    # SET_NULL preserves timetable if institution is deleted
    # Optional - allows system-wide default timetables
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, null=True, blank=True)
    
    # FIELD: Department Scope
    # Optionally limits timetable to specific department
    # SET_NULL preserves timetable if department is restructured
    # null=True allows institution-wide timetables
    department = models.ForeignKey('institution.Department', on_delete=models.CASCADE, null=True, blank=True)
    
    # FIELD: Course/Program Focus
    # Optionally focuses timetable on specific academic course
    # SET_NULL preserves timetable if course is discontinued
    # null=True allows broader departmental timetables
    course = models.ForeignKey('academics.Course', on_delete=models.CASCADE, null=True, blank=True)
    
    # FIELD: Branch Specialization
    # Optionally targets specific academic branch
    # SET_NULL preserves timetable if branch is deleted
    # null=True allows multi-branch timetables
    branch = models.ForeignKey('academics.Branch', on_delete=models.SET_NULL, null=True, blank=True)
    
    # FIELD: Creator/Owner
    # User who created this timetable (admin, scheduler, department head)
    # SET_NULL preserves timetable if user account is deleted
    # Tracks responsibility and modification permissions
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    # ============================================================================
    # TIMETABLE METADATA & STATUS
    # ============================================================================
    
    # FIELD: Timetable Name
    # Human-readable identifier for the timetable
    # Examples: "Fall 2024 Engineering", "Spring CS Schedule", "Weekly Timetable 1"
    # Default "My Timetable" for new schedules
    name = models.CharField(max_length=100, default="My Timetable")
    
    # FIELD: Publication Status
    # Tracks the current state of the timetable
    # Examples: "Draft", "Review", "Published", "Archived"
    # Default "Draft" for new timetables requiring review
    status = models.CharField(max_length=20, default='Draft', null=True, blank=True)
    
    # FIELD: Creation Timestamp
    # When the timetable was first created
    # auto_now_add=True sets once and never changes
    # Used for version tracking and historical records
    created_at = models.DateTimeField(auto_now_add=True)
    
    # FIELD: Active Status
    # Whether this timetable is currently being used
    # Default True for new timetables
    # False for archived or temporary timetables
    is_active = models.BooleanField(default=True)
    
    # FIELD: Published Status
    # Whether this timetable is visible to students and teachers
    # Default False - timetables must be explicitly published
    # Prevents accidental display of incomplete schedules
    is_published = models.BooleanField(default=False)
    
    # FIELD: Working Days Count
    # Number of days per week included in this timetable
    # Default 6 (Monday-Saturday, common in many institutions)
    # IntegerField allows flexibility for different week structures
    days_count = models.IntegerField(default=6)
    
    # ============================================================================
    # TIMETABLE BRANDING & FORMATTING
    # ============================================================================
    
    # FIELD: Primary Header
    # Main institutional name/title for printed timetables
    # Appears at the top of generated schedule documents
    # Default shows example institutional header
    heading_1 = models.CharField(max_length=255, default="L.J. INSTITUTE OF ENGINEERING AND TECHNOLOGY, L.J. UNIVERSITY")
    
    # FIELD: Secondary Header
    # Department/program specific information
    # Appears below primary header on printed timetables
    # Example: "DEPARTMENT OF COMPUTER SCIENCE - SEMESTER 4"
    heading_2 = models.CharField(max_length=255, default="SY CE/IT- 4 DEPARTMENT")
    
    # ============================================================================
    # FOOTER INFORMATION (for printed timetables)
    # ============================================================================
    
    # FIELD: Semester Information
    # Semester/term identifier for footer section
    # Examples: "SEMESTER III", "Fall 2024", "Term 1"
    # Appears in footer of printed timetables
    footer_semester_text = models.CharField(max_length=100, default="SEMESTER III")
    
    # FIELD: Preparation Credits
    # Names of people who prepared/created the timetable
    # TextField supports multi-line text with names and titles
    # Used for accountability and contact information
    footer_prepared_by = models.TextField(default="Prepared By:\nProf. Darshan Bhatt (DVB)\nProf. Priyanka Sinha (PCS)")
    
    # FIELD: Department Head Information
    # HOD (Head of Department) name and designation
    # TextField supports multi-line contact information
    # Provides official approval signature line for printed timetables
    footer_hod = models.TextField(default="Prof. Sneha Shah\nHOD- SY4 (CST/CSIT/CSE_CS/MA&CP)")
    
    # FIELD: Visual Theme
    # Color scheme and styling theme for timetable display
    # Examples: "classic", "modern", "minimalist", "colorful"
    # Default "classic" for traditional institutional appearance
    theme_palette = models.CharField(max_length=20, default="classic")

    def __str__(self):
        """
        STRING REPRESENTATION:
        Returns timetable identifier with name and creation timestamp.
        
        FORMAT: "NAME (YYYY-MM-DD HH:MM)"
        EXAMPLES:
        - "Fall 2024 Engineering (2024-08-15 09:30)"
        - "Spring CS Schedule (2024-01-20 14:45)"
        
        Provides clear identification for admin interface and debugging.
        Timestamp helps distinguish between multiple versions.
        """
        return f"{self.name} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"


class Room(models.Model):
    """
    WHAT THIS MODEL REPRESENTS:
    Physical classroom locations available for scheduling classes.
    Represents real spaces where teaching and learning occur.
    
    PURPOSE:
    - Track available classroom resources
    - Prevent double-booking of physical spaces
    - Support room capacity and equipment planning
    - Enable location-based scheduling optimization
    - Provide clear room identification on schedules
    
    ROOM IDENTIFICATION:
    Rooms use alphanumeric codes that are meaningful to the institution:
    - Building-Floor-Room: "410-C" (4th floor, room 10, building C)
    - Simple numbers: "101", "205", "Lab-A"
    - Descriptive names: "Main Hall", "Computer Lab", "Auditorium"
    
    SCHEDULING IMPORTANCE:
    - Physical constraint: Only one class per room per time slot
    - Capacity planning: Match room size to class size
    - Equipment needs: Lab rooms for practical subjects
    - Location optimization: Minimize student/teacher movement
    
    RELATIONSHIPS:
    - Room belongs to Institution (required for multi-tenant support)
    - Room used in multiple TimetableEntries across different time slots
    - One Room can host different subjects/divisions at different times
    """
    
    # FIELD: Institution Ownership
    # Links room to its parent institution for multi-tenant system
    # CASCADE means deleting institution also deletes all its rooms
    # Optional field allows system-wide rooms if needed
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, null=True, blank=True)
    
    # FIELD: Room Identifier
    # Short code or name that uniquely identifies the room
    # Examples: "410-C", "Lab-1", "Auditorium", "101", "Chemistry Lab"
    # 20 characters handles various naming conventions
    # help_text provides guidance for data entry
    number = models.CharField(max_length=20, help_text="e.g., 410-C")

    def __str__(self):
        """
        STRING REPRESENTATION:
        Returns the room identifier for display throughout the system.
        
        EXAMPLES:
        - "410-C"
        - "Computer Lab"
        - "Main Auditorium"
        
        Simple and clear identification for schedules and booking systems.
        """
        return self.number


class Division(models.Model):
    """
    WHAT THIS MODEL REPRESENTS:
    Student groups or classes that need to be scheduled together.
    Represents collections of students who take classes as a unit.
    
    PURPOSE:
    - Group students for scheduling purposes
    - Enable parallel section management (Division A, B, C)
    - Support manageable class sizes
    - Facilitate resource allocation and teacher assignment
    - Enable group-based academic tracking
    
    DIVISION EXAMPLES:
    - Academic divisions: "Division A", "Division B", "Batch 1"
    - Specialization groups: "CS-1", "IT-2", "ECE-A"
    - Size-based groups: "Group 1", "Section A", "Class 30"
    
    EDUCATIONAL BENEFITS:
    - Smaller groups: Better teacher-student interaction
    - Parallel sections: Accommodate large enrollments
    - Flexible grouping: Different subjects, different divisions
    - Timetable optimization: Distribute resources effectively
    
    RELATIONSHIPS:
    - Division belongs to Timetable (required for organization)
    - Division appears in multiple TimetableEntries (different subjects/times)
    - Students are assigned to Divisions (via student.models)
    """
    
    # FIELD: Parent Timetable
    # Links division to its organizing timetable
    # CASCADE means deleting timetable also deletes all its divisions
    # related_name='divisions' allows reverse lookup from timetable
    # Optional field allows standalone divisions if needed
    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name='divisions', null=True, blank=True)
    
    # FIELD: Division Name
    # Short identifier for the student group
    # Examples: "D1", "Division A", "Batch-1", "CS-Group1"
    # 10 characters handles most division naming conventions
    # help_text provides guidance for consistent naming
    name = models.CharField(max_length=10, help_text="e.g., D1")

    def __str__(self):
        """
        STRING REPRESENTATION:
        Returns the division name for display in schedules and forms.
        
        EXAMPLES:
        - "D1"
        - "Division A"
        - "CS-Group1"
        
        Clear identification for timetable entries and student assignment.
        """
        return self.name


class TimeSlot(models.Model):
    """
    WHAT THIS MODEL REPRESENTS:
    Individual time periods within a daily schedule.
    Defines when classes occur and their duration.
    
    PURPOSE:
    - Structure the daily academic schedule
    - Define lecture periods and break times
    - Enable consistent timing across the institution
    - Support different schedule patterns (45min, 60min lectures)
    - Provide framework for automatic timetable generation
    
    TIME SLOT EXAMPLES:
    - Lecture 1: 09:00-09:50 (50 minutes)
    - Lecture 2: 09:50-10:40 (50 minutes) 
    - Break: 10:40-11:00 (20 minutes)
    - Lecture 3: 11:00-11:50 (50 minutes)
    
    SCHEDULING IMPORTANCE:
    - Standardization: All classes follow same time structure
    - Efficiency: Optimal use of daily time
    - Break planning: Scheduled rest periods for students/teachers
    - Conflict prevention: Clear time boundaries prevent overlaps
    
    RELATIONSHIPS:
    - TimeSlot belongs to Timetable (required for organization)
    - TimeSlot used in multiple TimetableEntries (different days/divisions)
    - Multiple TimeSlots per Timetable (complete daily schedule)
    """
    
    # FIELD: Parent Timetable
    # Links time slot to its organizing timetable
    # CASCADE means deleting timetable also deletes all its time slots
    # related_name='timeslots' allows reverse lookup from timetable
    # Optional field allows reusable time slot templates
    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name='timeslots', null=True, blank=True)
    
    # DAY CHOICES: Days of the week for scheduling
    # Standard weekdays commonly used in academic institutions
    # Three-letter codes for database storage efficiency
    DAY_CHOICES = [
        ('MON', 'Monday'),     # Start of academic week
        ('TUE', 'Tuesday'),    # Regular teaching day
        ('WED', 'Wednesday'),  # Mid-week teaching day
        ('THU', 'Thursday'),   # Regular teaching day  
        ('FRI', 'Friday'),     # End of regular week
        ('SAT', 'Saturday'),   # Optional/half day in many institutions
    ]
    
    # FIELD: Lecture Sequence Number
    # Numerical order of this lecture within the daily schedule
    # Examples: 1, 2, 3, 4, 5, 6 (for 6 lectures per day)
    # IntegerField allows flexible numbering schemes
    # help_text provides guidance for sequential numbering
    lecture_number = models.IntegerField(help_text="1, 2, 3...")
    
    # FIELD: Period Start Time
    # When this lecture/break period begins
    # TimeField uses HH:MM format (24-hour)
    # Examples: 09:00, 10:30, 14:15
    start_time = models.TimeField()
    
    # FIELD: Period End Time
    # When this lecture/break period ends
    # TimeField uses HH:MM format (24-hour)
    # Examples: 09:50, 10:20, 15:05
    end_time = models.TimeField()
    
    # FIELD: Break Period Indicator
    # Boolean flag indicating if this is a break (recess/lunch) period
    # Default False = regular lecture period
    # True = break time (no classes scheduled)
    is_break = models.BooleanField(default=False)

    class Meta:
        """
        META CLASS CONFIGURATION:
        
        ordering: Default sort order for time slot queries
        - ['lecture_number'] sorts by sequence number in ascending order
        - Ensures time slots appear in chronological order
        - Important for generating correct daily schedules
        """
        ordering = ['lecture_number']

    def __str__(self):
        """
        STRING REPRESENTATION:
        Returns formatted time slot information showing sequence and duration.
        
        FORMAT: "Rec LECTURE_NUMBER: START_TIME - END_TIME"
        EXAMPLES:
        - "Rec 1: 09:00 - 09:50"
        - "Rec 2: 09:50 - 10:40"
        - "Rec 3: 11:00 - 11:50" (after break)
        
        "Rec" stands for "Recess" or lecture period.
        Clear time display helps with schedule planning and conflict detection.
        """
        return f"Rec {self.lecture_number}: {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"


class TimetableEntry(models.Model):
    """
    WHAT THIS MODEL REPRESENTS:
    A specific scheduling assignment that brings together all components:
    who (teacher + students), what (subject), when (day + time), where (room).
    
    PURPOSE:
    - Create specific class assignments
    - Prevent scheduling conflicts through constraints
    - Connect all scheduling components in one record
    - Enable automatic timetable generation and optimization
    - Support detailed schedule queries and reporting
    
    ENTRY COMPONENTS:
    Each TimetableEntry represents one scheduled class session:
    - WHO: Teacher (faculty) and student Division
    - WHAT: Subject (Course) being taught
    - WHEN: Day of week and TimeSlot (specific period)
    - WHERE: Room (physical location)
    
    CONFLICT PREVENTION:
    Built-in unique constraints prevent double-booking:
    - Same room cannot have two classes simultaneously
    - Same division cannot be in two places simultaneously
    - Same faculty cannot teach two classes simultaneously
    
    RELATIONSHIPS:
    - TimetableEntry belongs to Timetable (organization)
    - TimetableEntry references TimeSlot, Division, Course, Teacher, Room
    - Multiple TimetableEntries create complete weekly schedule
    """
    
    # FIELD: Parent Timetable
    # Links entry to its organizing timetable container
    # CASCADE means deleting timetable also deletes all its entries
    # related_name='entries' allows reverse lookup from timetable
    # Required field - every entry must belong to a timetable
    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name='entries')
    
    # FIELD: Day of Week
    # Which day this class session occurs
    # Uses same DAY_CHOICES as TimeSlot for consistency
    # 3 characters for three-letter day codes (MON, TUE, etc.)
    day = models.CharField(max_length=3, choices=TimeSlot.DAY_CHOICES)
    
    # ============================================================================
    # SCHEDULING COMPONENT RELATIONSHIPS
    # ============================================================================
    
    # FIELD: Time Period
    # When during the day this class occurs
    # CASCADE means deleting time slot also deletes entries using it
    # Required field - every entry must have a specific time
    timeslot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    
    # FIELD: Student Group
    # Which division/class group attends this session
    # CASCADE means deleting division also deletes its schedule entries
    # Required field - every entry must have assigned students
    division = models.ForeignKey(Division, on_delete=models.CASCADE)
    
    # FIELD: Subject/Course
    # What subject is being taught in this session
    # CASCADE means deleting course also deletes its schedule entries
    # Optional field - allows placeholder entries for planning
    subject = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True)
    
    # FIELD: Assigned Teacher
    # Which faculty member teaches this session
    # SET_NULL preserves entry if teacher is deleted (allows reassignment)
    # Optional field - allows unassigned slots for planning
    faculty = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    
    # FIELD: Physical Location
    # Where this class session takes place
    # SET_NULL preserves entry if room is deleted (allows relocation)
    # Optional field - allows TBD (To Be Determined) room assignments
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        """
        META CLASS CONFIGURATION:
        
        verbose_name_plural: Proper plural form for admin interface
        - "Timetable Entries" instead of default "Timetable Entrys"
        - Ensures correct English grammar in admin interface
        
        indexes: Database performance optimization
        - Index on 'division': Fast queries for division-specific schedules
        - Index on 'timeslot': Fast queries for time-based conflicts
        - Improves performance for schedule generation and conflict checking
        
        unique_together: Conflict prevention constraints
        - ('room', 'timeslot', 'day'): Prevents room double-booking
        - ('division', 'timeslot', 'day'): Prevents student group double-booking
        - ('faculty', 'timeslot', 'day'): Prevents teacher double-booking
        
        These constraints ensure scheduling integrity and prevent conflicts.
        """
        verbose_name_plural = "Timetable Entries"
        
        # Database indexes for performance optimization
        indexes = [
            models.Index(fields=['division']),   # Fast division-based queries
            models.Index(fields=['timeslot']),   # Fast time-based queries
        ]
        
        # Unique constraints to prevent scheduling conflicts
        unique_together = [
            ('room', 'timeslot', 'day'),         # No room double-booking
            ('division', 'timeslot', 'day'),     # No student group double-booking  
            ('faculty', 'timeslot', 'day'),      # No teacher double-booking
        ]
    
    def __str__(self):
        """
        STRING REPRESENTATION:
        Returns entry identifier showing day, time, and student group.
        
        FORMAT: "DAY - TIMESLOT - DIVISION"
        EXAMPLES:
        - "MON - Rec 1: 09:00 - 09:50 - D1"
        - "TUE - Rec 3: 11:00 - 11:50 - Division A"
        - "WED - Rec 2: 09:50 - 10:40 - CS-Group1"
        
        Clear identification for schedule management and debugging.
        Shows the core scheduling information at a glance.
        """
        return f"{self.day} - {self.timeslot} - {self.division}"
