from .models import News, Institution

def news_processor(request):
    """
    Makes news_list and dashboard_url available to all templates.
    """
    news_list = []
    dashboard_url = 'landing'  # safe fallback

    if request.user.is_authenticated:
        # Resolve correct dashboard URL based on role
        try:
            role = request.user.userprofile.role
            if role == 'institution_admin':
                dashboard_url = 'institution_admin_dashboard'
            elif role == 'teacher':
                dashboard_url = 'teacher_dashboard'
            elif role == 'student':
                dashboard_url = 'student_dashboard'
        except Exception:
            pass

        # Fetch news for the user's institution
        try:
            inst = Institution.objects.get(admin=request.user)
            news_list = News.objects.filter(institution=inst).order_by('-created_at')
        except Institution.DoesNotExist:
            news_list = News.objects.all().order_by('-created_at')

    return {'news_list': news_list, 'dashboard_url': dashboard_url}
