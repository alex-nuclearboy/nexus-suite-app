from django.urls import path
from . import views

app_name = "newsapp"

urlpatterns = [
    path('', views.MainView.as_view(), name='index'),
    path(
        'news/<str:category>/',
        views.NewsView.as_view(),
        name='news_by_category'
    ),
    path(
        'exchange-rates/',
        views.ExchangeRatesView.as_view(),
        name='exchange_rates'
    ),
    path(
        'convert-currency/',
        views.ConvertCurrencyView.as_view(),
        name='convert_currency'
    ),
    path(
        'weather/',
        views.WeatherView.as_view(),
        name='weather'
    ),
    path(
        'set_timezone/',
        views.set_timezone,
        name='set_timezone'
    ),
]
