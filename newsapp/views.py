from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render
from django.utils import timezone
from django.http import JsonResponse

from opencage.geocoder import OpenCageGeocode

from datetime import datetime
import requests
import pytz
import os

from .translations import translations
from .utils.utils import get_translated_day_and_month

# API Keys
NEWS_API_KEY = os.getenv('NEWS_API_ORG_KEY')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
GEOCODING_API_KEY = os.getenv('GEOCODING_API_KEY')

# Initialize geocoder
geocoder = OpenCageGeocode(GEOCODING_API_KEY)

# News Categories
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

# Country Names
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

COUNTRIES_GENITIVE_UA = {
    'ua': 'України',
    'us': 'США',
    'gb': 'Великої Британії',
    'fr': 'Франції',
    'de': 'Німеччини',
    'pl': 'Польщі'
}


def get_language(request):
    """
    Get the language from the request or session.
    - Retrieves the language from the GET parameters or session.
    - Defaults to English if no language is found.
    - Stores the language in the session.

    Parameters:
    request (HttpRequest): The request object.

    Returns:
    str: The language code.
    """
    language = request.GET.get('lang')
    if not language:
        language = request.session.get('language', 'en')
    request.session['language'] = language
    return language


def set_timezone(request):
    """
    Set the timezone based on the user's request.
    - Retrieves the 'timezone' parameter from the GET request.
    - Activates the timezone if it is valid.
    - Stores the timezone in the user's session.
    - Handles invalid timezone errors gracefully.

    Parameters:
    request (HttpRequest): The request containing the 'timezone' parameter
                           in the GET query string.

    Returns:
    JsonResponse: A response with a JSON object containing the status
                  of the operation.
    """
    timezone_str = request.GET.get('timezone')
    if timezone_str:
        try:
            timezone.activate(pytz.timezone(timezone_str))
            request.session['django_timezone'] = timezone_str
        except pytz.UnknownTimeZoneError:
            pass
    return JsonResponse({'status': 'success'})


def main(request):
    """
    Main view function to display the weather, exchange rates, and news.
    - Displays current date and time in the user's timezone.
    - Retrieves the language from the session.
    - Loads the translations based on the language.
    - Retrieves and paginates news data based on country.
    - Fetches the weather and exchange rates data.
    - Handles errors and displays appropriate messages.

    Parameters:
    request (HttpRequest): The request object containing GET parameters
                           for 'country', and 'page'.

    Returns:
    HttpResponse: The rendered template with the context data.
    """
    language = get_language(request)
    trans = translations.get(language, translations['en'])

    timezone_str = request.session.get('django_timezone', 'UTC')
    user_timezone = pytz.timezone(timezone_str)
    now = timezone.now().astimezone(user_timezone)

    translated_day, translated_month = get_translated_day_and_month(now,
                                                                    language)
    current_time = now.strftime('%H:%M')
    current_date = f"{translated_day}, {now.day} {translated_month} {now.year}"

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
    genitive_country_name = (
        COUNTRIES_GENITIVE_UA.get(country, 'Unknown') if language == 'uk'
        else COUNTRIES.get(country, 'Unknown')
    )

    try:
        weather_data = fetch_weather(city, trans, language)
    except ValueError as ve:
        weather_error_message = str(ve)
        weather_data = None
    except requests.RequestException as e:
        weather_error_message = (
            trans['unable_to_retrieve_weather'] % {'error': str(e)}
        )
        weather_data = None

    exchange_rates = fetch_exchange_rates()

    news_data = fetch_news(category, country, trans)

    # Pagination of news
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
        'genitive_country_name': genitive_country_name,
        'error_message': error_message,
        'weather_error_message': weather_error_message,
    }
    return render(request, 'newsapp/index.html', context)


def get_city_name_in_english(city_name):
    """
    Convert city name to English using OpenCage Geocoding API.

    Parameters:
    city_name (str): The city name to be translated.

    Returns:
    str: The city name in English.
    """
    results = geocoder.geocode(city_name, language='en')
    if results and len(results):
        return results[0]['components'].get('city') or \
               results[0]['components'].get('town') or \
               results[0]['components'].get('village')
    else:
        raise ValueError(f"Could not geocode city name: {city_name}")


def fetch_weather(city, trans, lang='en'):
    """
    Fetch weather data from WeatherAPI.
    - Retrieves weather data for the specified city.
    - Uses the language parameter to get the data in the desired language.
    - Raises a ValueError if the city is not found.

    Parameters:
    city (str): The name of the city.
    trans (dict): The translation dictionary.
    lang (str): The language code.

    Returns:
    dict: The weather data.
    """
    try:
        city_in_english = get_city_name_in_english(city)
    except ValueError:
        city_in_english = city  # Use original name if translation fails

    url = (
        f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}"
        f"&q={city_in_english}&lang={lang}"
    )
    response = requests.get(url)
    data = response.json()

    if response.status_code != 200:
        error_msg = data.get('error', {}).get('message', 'Unknown error')
        if response.status_code == 401:
            raise ValueError(trans['invalid_key'])
        if response.status_code == 400:
            raise ValueError(trans['city_not_found'] % {'city': city})
        raise ValueError(
            trans['unable_to_retrieve_weather'] % {'error': error_msg}
        )

    weather_data = {
        'temperature': round(data['current']['temp_c']),
        'humidity': data['current']['humidity'],
        'wind': round(data['current']['wind_kph'] / 3.6, 2),  # Convert to m/s
        'pressure': round(data['current']['pressure_mb'] * 0.750062),  # Convert to mmHg
        'condition': data['current']['condition']['text'],
        'icon_url': f"http:{data['current']['condition']['icon']}",
        'update_time': (
            datetime.fromisoformat(data['current']['last_updated'])
            .strftime('%H:%M')
        )
    }

    return weather_data


def fetch_exchange_rates():
    """
    Fetch exchange rates data from PrivatBank API.
    - Retrieves the exchange rates for the required currencies.

    Returns:
    list: A list of exchange rates for the required currencies.
    """
    today = datetime.today().strftime('%d.%m.%Y')
    url = f'https://api.privatbank.ua/p24api/exchange_rates?json&date={today}'
    response = requests.get(url)
    data = response.json()
    required_currencies = ['USD', 'EUR', 'PLN']

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

    Parameters:
    category (str): The news category.
    country (str): The country code.
    trans (dict): The translation dictionary.

    Returns:
    list: A list of news articles.
    """
    # Translate the category into English if necessary
    if category in CATEGORY_MAP.values():
        category = list(CATEGORY_MAP.keys())[
            list(CATEGORY_MAP.values()).index(category)
        ]

    url = (
        f'https://newsapi.org/v2/top-headlines?country={country}'
        f'&category={category}&apiKey={NEWS_API_KEY}'
    )
    response = requests.get(url)
    data = response.json()
    if response.status_code != 200:
        raise ValueError(
            trans['error_fetching_news']
            % {'error': data.get('message', 'Unknown error')}
        )
    return data['articles']
