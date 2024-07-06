from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render

import urllib.parse
import requests
from datetime import datetime
import pytz
import os

from .translations import translations
from .utils.utils import get_translated_day_and_month

NEWS_API_KEY = os.getenv('NEWS_API_ORG_KEY')
WEATHER_API_KEY = os.getenv('OPEN_WEATHER_API_KEY')

CATEGORIES = {
    'en': [
        'general', 'business', 'entertainment',
        'health', 'science', 'sports', 'technology'
    ],
    'uk': [
        'загальні', 'бізнес', 'розваги',
        'здоров\'я', 'наука', 'спорт', 'технології'
    ]
}
CATEGORY_MAP = {
    'general': 'загальні',
    'business': 'бізнес',
    'entertainment': 'розваги',
    'health': 'здоров\'я',
    'science': 'наука',
    'sports': 'спорт',
    'technology': 'технології'
}
COUNTRIES = {
    'ua': 'Ukraine',
    'us': 'USA',
    'gb': 'United Kingdom',
    'fr': 'France',
    'de': 'Germany',
    'pl': 'Poland'
}
COUNTRIES_UA = {
    'ua': 'Україна',
    'us': 'США',
    'gb': 'Велика Британія',
    'fr': 'Франція',
    'de': 'Німеччина',
    'pl': 'Польща'
}


def get_language(request):
    """
    Get the language from the request or session.
    - Retrieves the language from the GET parameters or session.
    - Defaults to English if no language is found.
    - Stores the language in the session.
    """
    language = request.GET.get('lang')
    if not language:
        language = request.session.get('language', 'en')
    request.session['language'] = language
    return language


def get_timezone(request):
    """
    Get the timezone from the request or session.
    - Retrieves the timezone from the GET parameters or session.
    - Defaults to 'UTC' if no timezone is found.
    - Stores the timezone in the session.
    """
    timezone = request.GET.get('timezone')
    if not timezone:
        timezone = request.session.get('timezone', 'UTC')
    request.session['timezone'] = timezone
    return timezone


def main(request):
    """
    Main view function to display the weather and exchange rates.
    - Retrieves the language from the session.
    - Loads the translations based on the language.
    - Fetches the weather and exchange rates data.
    - Handles errors and displays appropriate messages.
    """
    language = get_language(request)
    trans = translations.get(language, translations['en'])

    timezone_str = get_timezone(request)
    timezone = pytz.timezone(timezone_str)
    now = datetime.now(timezone)

    translated_day, translated_month = get_translated_day_and_month(now)
    current_time = now.strftime('%H:%M')
    current_date = f"{translated_day}, {translated_month} {now.day}, {now.year}"

    error_message = None
    weather_error_message = None
    default_city = 'Kyiv' if language == 'en' else 'Київ'
    city = request.GET.get('city', default_city)

    category = request.GET.get('category', 'general')
    country = request.GET.get('country', 'us' if language == 'en' else 'ua')

    # Translate the names of categories and countries to display
    displayed_category = (
        CATEGORY_MAP.get(category, category) if language == 'uk' else category
    )
    displayed_country_name = (
        COUNTRIES_UA.get(country, 'Unknown') if language == 'uk'
        else COUNTRIES.get(country, 'Unknown')
    )

    try:
        weather_data = fetch_weather(city, trans, language)
    except ValueError as ve:
        weather_error_message = str(ve)
        weather_data = None
    except requests.RequestException as e:
        weather_error_message = (
            trans['error_fetching_weather'] % {'error': str(e)}
        )
        weather_data = None

    exchange_rates = fetch_exchange_rates()

    news_data = fetch_news(category, country, trans)

    # Пагінація новин
    page = request.GET.get('page', 1)
    paginator = Paginator(news_data, 10)
    try:
        news_data = paginator.page(page)
    except PageNotAnInteger:
        news_data = paginator.page(1)
    except EmptyPage:
        news_data = paginator.page(paginator.num_pages)

    context = {
        'translations': trans,
        'current_date': current_date,
        'current_time': current_time,
        'categories': CATEGORIES[language],
        'countries': COUNTRIES if language == 'en' else COUNTRIES_UA,
        'news_data': news_data,
        'weather_data': weather_data,
        'exchange_rates': exchange_rates,
        'selected_category': displayed_category,
        'selected_city': city,
        'selected_country': country,
        'selected_country_name': displayed_country_name,
        'error_message': error_message,
        'weather_error_message': weather_error_message
    }
    return render(request, 'newsapp/index.html', context)


def fetch_weather(city, trans, language):
    """
    Fetch weather data from OpenWeatherMap API.
    - Retrieves weather data for the specified city.
    - Uses the language parameter to get the data in the desired language.
    - Raises a ValueError if the city is not found.
    """
    url = (
        f'https://api.openweathermap.org/data/2.5/weather?q={city}'
        f'&APPID={WEATHER_API_KEY}&units=metric&lang={language}'
    )
    response = requests.get(url)
    if response.status_code == 401:
        raise ValueError(
            trans['error_fetching_weather'] % {'error': 'Invalid API key'}
        )
    if response.status_code == 404:
        raise ValueError(trans['city_not_found'] % {'city': city})
    response.raise_for_status()
    data = response.json()
    return data


def fetch_exchange_rates():
    """
    Fetch exchange rates data from PrivatBank API.
    - Retrieves the exchange rates for the required currencies.
    """
    today = datetime.today().strftime('%d.%m.%Y')
    url = f'https://api.privatbank.ua/p24api/exchange_rates?json&date={today}'
    response = requests.get(url)
    data = response.json()
    required_currencies = ['EUR', 'USD', 'GBP', 'CHF', 'PLN']

    exchange_rates = [
        rate for rate in data['exchangeRate']
        if rate['currency'] in required_currencies
    ]
    exchange_rates.sort(key=lambda x: required_currencies.index(x['currency']))
    return exchange_rates


def fetch_news(category, country, trans):
    """
    Fetch news data from NewsAPI.
    - Retrieves news data for the specified category and country.
    - Raises a ValueError if there is an error fetching news.
    """
    # Translate the category into English if necessary
    if category in CATEGORY_MAP.values():
        category = list(CATEGORY_MAP.keys())[
            list(CATEGORY_MAP.values()).index(category)
        ]

    url = (
        f'https://newsapi.org/v2/top-headlines?country={country}'
        f'&category={urllib.parse.quote(category)}&apiKey={NEWS_API_KEY}'
    )
    response = requests.get(url)
    data = response.json()
    if response.status_code != 200:
        raise ValueError(
            trans['error_fetching_news']
            % {'error': data.get('message', 'Unknown error')}
        )
    return data['articles']
