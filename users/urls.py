from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('signup/', views.SignupUserView.as_view(), name='signup'),
    path('login/', views.LoginUserView.as_view(), name='login'),
    path('logout/', views.LogoutUserView.as_view(), name='logout'),
    path('profile/', views.UpdateUserProfileView.as_view(), name='profile'),
    path(
        'password_reset/',
        views.CustomPasswordResetRequestView.as_view(),
        name='password_reset'
    ),
    path(
        'password_reset/done/',
        views.CustomPasswordResetDoneView.as_view(),
        name='password_reset_done'
    ),
    path(
        'password/reset/<uidb64>/<token>/',
        views.CustomPasswordResetConfirmView.as_view(),
        name='password_reset_confirm'
    ),
    path(
        'password/reset/complete/',
        views.CustomPasswordResetCompleteView.as_view(),
        name='password_reset_complete'
    ),
]
