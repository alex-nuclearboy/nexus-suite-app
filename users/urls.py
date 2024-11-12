from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('signup/', views.SignupUserView.as_view(), name='signup'),
    path('login/', views.LoginUserView.as_view(), name='login'),
    path('logout/', views.LogoutUserView.as_view(), name='logout'),
    path('profile/', views.UpdateUserProfileView.as_view(), name='profile'),
]
