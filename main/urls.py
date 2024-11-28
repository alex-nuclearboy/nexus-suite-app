from django.urls import path
from . import views

urlpatterns = [
    path('random-quote/', views.random_quote_view, name='random_quote'),
]
