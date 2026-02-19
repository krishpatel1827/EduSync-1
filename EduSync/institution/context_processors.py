from .models import News, Institution

def news_processor(request):
    """
    Makes news_list available to all templates.
    """
    news_list = []
    if request.user.is_authenticated:
        # Try to find the institution associated with the user
        # This implementation might vary depending on how users are linked to institutions
        # For an admin, it's request.user.institution
        # For others, we might need a different lookup.
        # But for now, let's just get all news if we can't find a specific one, or filter by user's institution if possible.
        
        try:
            # Check if user is an admin of an institution
            inst = Institution.objects.get(admin=request.user)
            news_list = News.objects.filter(institution=inst).order_by('-created_at')
        except Institution.DoesNotExist:
            # Maybe the user is a student/teacher? 
            # If so, they should have an institution link.
            # Let's check accounts.UserProfile or similar if it exists.
            # For now, let's just return all news as a fallback if the project is simple,
            # or try to find any institution the user belongs to.
            news_list = News.objects.all().order_by('-created_at')
            
    return {'news_list': news_list}
