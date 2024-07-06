from django.urls import path
from . import views

app_name = "newsapp"

urlpatterns = [
    path('', views.main, name='index'),
    path('set_timezone/', views.set_timezone, name='set_timezone'),
]
