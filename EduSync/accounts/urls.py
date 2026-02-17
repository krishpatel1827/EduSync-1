from django.urls import path 
from . import views 
 
urlpatterns = [ 
    path('', views.landing_view, name='landing'), 
    path('login/', views.unified_login_view, name='login'), 
    path('signup/', views.signup_view, name='signup'), 
    path('logout/', views.logout_view, name='logout'), 
]
