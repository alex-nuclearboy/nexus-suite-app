from django.shortcuts import render
import requests
import datetime
import os

NEWS_API_KEY = os.getenv('NEWS_API_ORG_KEY')
WEATHER_API_KEY = os.getenv('OPEN_WEATHER_API_KEY')

CATEGORIES = [
    'general', 'business', 'entertainment',
    'health', 'science', 'sports', 'technology'
]
COUNTRIES = {
    'ua': 'Ukraine',
    'us': 'USA',
    'gb': 'United Kingdom',
    'fr': 'France',
    'de': 'Germany',
    'pl': 'Poland'
}


def main(request):
    error_message = None
    weather_error_message = None
    category = request.GET.get('category', 'general')
    city = request.GET.get('city', 'Kyiv')
    country = request.GET.get('country', 'ua')

    try:
        weather_data = fetch_weather(city)
    except ValueError as ve:
        weather_error_message = str(ve)
        weather_data = None
    except requests.RequestException as e:
        weather_error_message = (
            f"An error occurred while fetching weather data: {str(e)}"
        )
        weather_data = None

    news_data = fetch_news(category, country)
    exchange_rates = fetch_exchange_rates()
    selected_country_name = COUNTRIES.get(country, 'Unknown')

    context = {
        'categories': CATEGORIES,
        'countries': COUNTRIES,
        'news_data': news_data,
        'weather_data': weather_data,
        'exchange_rates': exchange_rates,
        'selected_category': category,
        'selected_city': city,
        'selected_country': country,
        'selected_country_name': selected_country_name,
        'error_message': error_message,
        'weather_error_message': weather_error_message
    }
    return render(request, 'newsapp/index.html', context)


def fetch_news(category, country):
    url = (
        f'https://newsapi.org/v2/top-headlines?country={country}'
        f'&category={category}&apiKey={NEWS_API_KEY}'
    )
    response = requests.get(url)
    data = response.json()
    if response.status_code != 200:
        raise ValueError(
            f"Error fetching news: {data.get('message', 'Unknown error')}"
        )
    return data['articles']


def fetch_weather(city):
    url = (
        f'https://api.openweathermap.org/data/2.5/weather?q={city}'
        f'&APPID={WEATHER_API_KEY}&units=metric'
    )
    response = requests.get(url)
    if response.status_code == 400:
        raise ValueError(f"City '{city}' not found.")
    response.raise_for_status()
    data = response.json()
    return data


def fetch_exchange_rates():
    today = datetime.datetime.today().strftime('%d.%m.%Y')
    url = f'https://api.privatbank.ua/p24api/exchange_rates?json&date={today}'
    response = requests.get(url)
    data = response.json()
    required_currencies = ['USD', 'EUR', 'GBP', 'CHF', 'PLN']

    exchange_rates = [
        rate for rate in data['exchangeRate']
        if rate['currency'] in required_currencies
    ]
    exchange_rates.sort(key=lambda x: required_currencies.index(x['currency']))
    return exchange_rates
