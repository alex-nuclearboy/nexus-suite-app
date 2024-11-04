from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('signup/', views.SignupUserView.as_view(), name='signup'),
    path('login/', views.LoginUserView.as_view(), name='login'),
    # path('logout/', views.logoutuser, name='logout'),
    # path('profile/', views.profile, name='profile'),
]
