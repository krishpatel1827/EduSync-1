# ================================================================================
# INSTITUTION APP - MODELS.PY  
# ================================================================================
# This file defines the database structure (models) for institution management.
# In Django, models are Python classes that represent database tables.
# Each model class becomes a table, and each class attribute becomes a column.
#
# WHAT ARE MODELS?
# Models define the structure and behavior of your data. They are the single,
# definitive source of truth about your data. Django uses models to:
# 1. Create database tables automatically
# 2. Generate database queries (SQL) automatically  
# 3. Validate data before saving to database
# 4. Define relationships between different types of data
#
# KEY CONCEPTS IN THIS FILE:
# - Institution: The main entity (school, college, university)
# - Department: Organizational units within an institution (Science, Arts, etc.)
# - News: Announcements and updates for the institution community
# - AcademicCalendarEvent: Important dates like exams, holidays, deadlines
#
# RELATIONSHIPS EXPLAINED:
# - OneToOneField: One-to-one relationship (1 institution has 1 admin user)
# - ForeignKey: One-to-many relationship (1 institution has many departments)
# - ManyToManyField: Many-to-many relationship (not used in this file)
# ================================================================================

# Import Django's database models module
from django.db import models
# Import Django's built-in User model for authentication
from django.contrib.auth.models import User


class Institution(models.Model):
    """
    WHAT THIS MODEL REPRESENTS:
    The main Institution model represents an educational institution (school, 
    college, university, etc.) in the EduSync system. This is the central entity
    that all other data relates to.
    
    WHY IS THIS IMPORTANT:
    - Each institution's data is completely separate from others (multi-tenancy)
    - All teachers, students, courses, etc. belong to one specific institution
    - Provides the foundation for the entire EduSync ecosystem
    
    BUSINESS RULES:
    - Each institution must have a unique name (no duplicates allowed)
    - Each institution must have exactly one administrator user
    - Each institution must have a unique email address
    - Phone, address, and established year are optional but recommended
    
    DATABASE TABLE NAME:
    Django will create a table named 'institution_institution'
    """
    
    # FIELD: Institution Name
    # CharField stores text up to 200 characters
    # unique=True means no two institutions can have the same name
    name = models.CharField(max_length=200, unique=True)
    
    # FIELD: Institution Administrator  
    # OneToOneField creates a 1:1 relationship with Django's User model
    # This means each institution has exactly one admin user, and each user
    # can only be admin of one institution
    # on_delete=models.CASCADE means if the User is deleted, delete the Institution too
    admin = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # FIELD: Contact Email
    # EmailField automatically validates that the value is a valid email format
    # unique=True ensures no two institutions can use the same email
    email = models.EmailField(unique=True)
    
    # FIELD: Phone Number
    # CharField for phone numbers (supports international formats)
    # blank=True means the field can be empty in forms
    # null=True means the database can store NULL values for this field
    phone = models.CharField(max_length=15, blank=True, null=True)
    
    # FIELD: Physical Address  
    # TextField can store large amounts of text (unlimited length)
    # Used for multi-line addresses
    # blank=True means this field is optional
    address = models.TextField(blank=True)
    
    # FIELD: Year Established
    # IntegerField stores integer numbers
    # Used to track when the institution was founded
    # Optional field (blank=True, null=True)
    established_year = models.IntegerField(blank=True, null=True)
    
    # FIELD: Creation Timestamp
    # DateTimeField stores both date and time
    # auto_now_add=True automatically sets this when the record is first created
    # This field is never updated after creation (different from auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        """
        WHAT THIS METHOD DOES:
        Defines how Institution objects are displayed as text.
        When you print an Institution object or view it in Django admin,
        this method determines what text is shown.
        
        RETURN VALUE:
        The institution's name as a string
        
        WHY IS THIS IMPORTANT:
        - Makes debugging easier (you see "Harvard University" instead of "<Institution object>")
        - Improves Django admin interface readability
        - Used in dropdown lists and form displays
        """
        return self.name


class Department(models.Model):
    """
    WHAT THIS MODEL REPRESENTS:
    Represents organizational departments within an institution (like Science,
    Mathematics, Arts, Engineering, etc.). Departments help organize teachers,
    students, and courses into logical groups.
    
    WHY DEPARTMENTS MATTER:
    - Organize large institutions into manageable units
    - Allow for department-specific policies and procedures
    - Enable specialized academic programs and curricula
    - Provide clear reporting and management structure
    
    RELATIONSHIP TO INSTITUTION:
    Each department belongs to exactly one institution (ForeignKey relationship).
    Each institution can have multiple departments (one-to-many relationship).
    
    DATABASE TABLE NAME:
    Django will create a table named 'institution_department'
    """
    
    # FIELD: Institution Reference
    # ForeignKey creates a many-to-one relationship
    # Many departments can belong to one institution
    # on_delete=models.CASCADE means if Institution is deleted, delete all its Departments
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)
    
    # FIELD: Department Name
    # CharField stores the department name (e.g., "Computer Science", "Biology")  
    # max_length=100 provides reasonable space for department names
    name = models.CharField(max_length=100)
    
    # FIELD: Department Description
    # TextField for detailed description of the department
    # Optional field (blank=True) for additional information
    description = models.TextField(blank=True)
    
    # FIELD: Creation Timestamp
    # Automatically set when department is created
    # Useful for tracking when departments were established
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """
        WHAT THIS METHOD DOES:
        Returns the department name for display purposes.
        
        EXAMPLES:
        "Computer Science", "Mathematics", "English Literature"
        """
        return self.name

    class Meta:
        """
        META CLASS: Additional options for the Department model
        
        WHAT IS Meta CLASS:
        The Meta class contains metadata about the model - options that
        affect how Django handles the model but aren't database fields.
        
        OPTIONS EXPLAINED:
        - unique_together: Ensures no institution has duplicate department names
          This creates a compound unique constraint on (institution, name)
          Meaning: Harvard can have "Computer Science" and MIT can have "Computer Science"
          But Harvard cannot have two "Computer Science" departments
        """
        unique_together = ('institution', 'name')


class News(models.Model):
    """
    WHAT THIS MODEL REPRESENTS:
    Stores news announcements and updates that institutions want to share
    with their community (teachers, students, parents, etc.).
    
    USE CASES:
    - Important announcements (schedule changes, events, etc.)
    - Academic updates (exam schedules, results, etc.)
    - Administrative notices (policy changes, deadlines, etc.)
    - Emergency communications (weather closures, safety alerts, etc.)
    
    DISPLAY BEHAVIOR:
    News items are typically displayed in reverse chronological order
    (newest first) on dashboards and news feeds.
    
    DATABASE TABLE NAME:
    Django will create a table named 'institution_news'
    """
    
    # FIELD: Institution Reference
    # ForeignKey links each news item to a specific institution
    # related_name='news_feed' allows reverse lookup: institution.news_feed.all()
    # null=True allows news items that aren't linked to institutions (legacy compatibility)
    # on_delete=models.CASCADE means deleting institution deletes all its news
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='news_feed', null=True)
    
    # FIELD: News Content
    # TextField stores the actual news text (unlimited length)
    # Can contain announcements, updates, or any textual content
    content = models.TextField()
    
    # FIELD: Publication Timestamp
    # Automatically set when news item is created
    # Used for sorting news items chronologically
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """
        WHAT THIS METHOD DOES:
        Returns the first 30 characters of the news content for display.
        This provides a preview of the news item in lists and admin interface.
        
        EXAMPLE:
        If content is "The spring semester will begin on Monday, January 15th..."
        This returns "The spring semester will begin"
        
        WHY TRUNCATE TO 30 CHARACTERS:
        - Keeps displays clean and readable
        - Prevents long news items from breaking layouts
        - Provides enough text for identification
        """
        return self.content[:30]


class AcademicCalendarEvent(models.Model):
    """
    WHAT THIS MODEL REPRESENTS:
    Stores important academic dates and events for an institution's calendar.
    This includes exams, holidays, semester dates, deadlines, and other
    significant academic events.
    
    PURPOSE:
    - Provides centralized calendar management for institutions
    - Helps students and faculty plan their schedules
    - Ensures important dates are communicated clearly
    - Supports different types of academic events
    
    BUSINESS RULES:
    - Each event belongs to one institution
    - Events can span multiple days (start_date to end_date)
    - Single-day events can omit end_date
    - Events can be published or kept as drafts
    - Events are sorted by date for chronological display
    
    DATABASE TABLE NAME:
    Django will create a table named 'institution_academiccalendarevent'
    """
    
    # FIELD: Event Type Choices
    # Defines the possible types of academic events
    # This is a list of tuples: (database_value, human_readable_display)
    EVENT_TYPES = [
        ('exam', 'Examination'),           # Exams and assessments
        ('holiday', 'Holiday'),            # Institutional holidays
        ('semester_start', 'Semester Start'),  # Beginning of academic terms
        ('semester_end', 'Semester End'),      # End of academic terms  
        ('event', 'Event'),                    # General academic events
        ('deadline', 'Deadline'),              # Important deadlines
        ('other', 'Other'),                    # Miscellaneous events
    ]
    
    # FIELD: Institution Reference
    # Links each calendar event to a specific institution
    # related_name='calendar_events' enables: institution.calendar_events.all()
    # on_delete=models.CASCADE removes events when institution is deleted
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='calendar_events')
    
    # FIELD: Event Title
    # Short, descriptive name for the event
    # Examples: "Final Exams", "Spring Break", "Registration Deadline"
    title = models.CharField(max_length=200)
    
    # FIELD: Event Description  
    # Detailed information about the event
    # Optional field for additional context and details
    description = models.TextField(blank=True)
    
    # FIELD: Event Type
    # CharField with predefined choices from EVENT_TYPES
    # Helps categorize and filter events
    # Default value is 'event' for general events
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='event')
    
    # FIELD: Start Date
    # DateField stores just the date (no time component)
    # Required field - every event must have a start date
    start_date = models.DateField()
    
    # FIELD: End Date
    # Optional end date for multi-day events
    # null=True and blank=True make this field optional
    # Single-day events can leave this empty
    end_date = models.DateField(null=True, blank=True)
    
    # FIELD: Publication Status
    # BooleanField stores True/False values
    # Controls whether event is visible to users or kept as draft
    # Default False means events must be explicitly published
    is_published = models.BooleanField(default=False)
    
    # FIELD: Creation Timestamp
    # Automatically set when event is first created
    # Never changes after creation
    created_at = models.DateTimeField(auto_now_add=True)
    
    # FIELD: Last Modified Timestamp  
    # Automatically updated every time the event is saved
    # auto_now=True updates this field on every save() operation
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        """
        META CLASS: Additional configuration for AcademicCalendarEvent model
        
        ORDERING:
        Specifies default sort order for queries
        ['start_date', 'title'] means:
        1. Sort by start_date first (earliest dates first)
        2. If start_dates are the same, sort by title alphabetically
        
        This ensures calendar events always appear in chronological order
        with consistent sub-sorting for same-day events.
        """
        ordering = ['start_date', 'title']
    
    def __str__(self):
        """
        WHAT THIS METHOD DOES:
        Returns a formatted string representation of the calendar event.
        
        FORMAT:
        "Event Title (YYYY-MM-DD)"
        
        EXAMPLES:
        "Final Exams (2024-05-15)"
        "Spring Break (2024-03-11)"
        "Registration Deadline (2024-01-10)"
        
        WHY INCLUDE THE DATE:
        - Provides immediate context about when the event occurs
        - Helps distinguish between recurring events (e.g., multiple exam periods)
        - Makes event lists more informative and scannable
        """
        return f"{self.title} ({self.start_date})"
