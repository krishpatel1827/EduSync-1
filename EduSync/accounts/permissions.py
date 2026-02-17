from rest_framework.permissions import BasePermission


class IsStudent(BasePermission):
    """
    Permission class that only allows students to access the view.
    """
    message = "Only students can access this resource."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'student'


class IsTeacher(BasePermission):
    """
    Permission class that only allows teachers to access the view.
    """
    message = "Only teachers can access this resource."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'teacher'


class IsInstitutionAdmin(BasePermission):
    """
    Permission class that only allows institution admins to access the view.
    """
    message = "Only institution administrators can access this resource."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'institution_admin'


class IsTeacherOrAdmin(BasePermission):
    """
    Permission class that allows teachers or institution admins.
    """
    message = "Only teachers or administrators can access this resource."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if not hasattr(request.user, 'userprofile'):
            return False
        return request.user.userprofile.role in ['teacher', 'institution_admin']


class IsSameInstitution(BasePermission):
    """
    Permission class that checks if the user belongs to the same institution
    as the resource they're trying to access.
    
    Requires the view to have a `get_institution_name` method or the object
    to have an `institution` attribute.
    """
    message = "You can only access resources from your own institution."

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        if not hasattr(request.user, 'userprofile'):
            return False
        
        user_institution = request.user.userprofile.institution.lower()
        
        # Check if view has custom method
        if hasattr(view, 'get_institution_name'):
            obj_institution = view.get_institution_name(obj).lower()
        # Check common attribute names
        elif hasattr(obj, 'institution'):
            obj_institution = (obj.institution.name if hasattr(obj.institution, 'name') else str(obj.institution)).lower()
        elif hasattr(obj, 'institution_name'):
            obj_institution = obj.institution_name.lower()
        else:
            return False
        
        return user_institution == obj_institution
