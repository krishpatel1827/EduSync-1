from django.urls import path
from .views import landing, signup, login_view

urlpatterns = [
    path('', landing, name='landing'),
    path('signup/', signup, name='signup'),
    path('login/', login_view, name='login'),
]
