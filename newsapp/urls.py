from django.urls import path
from . import views

app_name = "newsapp"

urlpatterns = [
    path('', views.main, name='index'),
]
