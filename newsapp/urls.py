from django.urls import path
from . import views

app_name = "newsapp"

urlpatterns = [
    path('', views.main, name='index'),
    path('news/<str:category>/', views.news_by_category, name='news_by_category'),
    path('exchange-rates/', views.exchange_rates_page, name='exchange_rates'),
    path('convert-currency/', views.convert_currency_view, name='convert_currency'),
    path('weather/', views.weather_page, name='weather'),
    path('set_timezone/', views.set_timezone, name='set_timezone'),
]
