from institution.models import Institution

def get_user_institution(user):
    """
    Retrieves the Institution associated with a given User.
    Supports Institution Admins, Teachers, Students, and UserProfiles.
    Returns None if no institution is found or user is not authenticated.
    """
    if not user or not user.is_authenticated:
        return None
    
    # 1. Check if user is an Institution Admin (OneToOne relation)
    try:
        return Institution.objects.get(admin=user)
    except Institution.DoesNotExist:
        pass
    
    # 2. Check if user is a Teacher
    if hasattr(user, 'teacher'):
        return user.teacher.institution
        
    # 3. Check if user is a Student
    if hasattr(user, 'student'):
        return user.student.institution
        
    # 4. Fallback to UserProfile string check
    if hasattr(user, 'userprofile'):
        inst_name = user.userprofile.institution
        if inst_name:
            return Institution.objects.filter(name__iexact=inst_name).first()
            
    return None
