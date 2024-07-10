from django.shortcuts import render, redirect
from django.utils import timezone
from django.http import JsonResponse
from django.core.cache import cache

from datetime import datetime
import requests
import pytz
import os

from .translations import translations
from .utils.utils import get_translated_day_and_month, fetch_news_by_category
from .utils.location_utils import get_city_and_country_info, get_country_name

# API Keys
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

# News Categories
CATEGORIES = {
    'en': [
        'general', 'business', 'entertainment', 'health',
        'science', 'sports', 'technology',
    ],
    'uk': [
        'загальні', 'бізнес',  'розваги', 'здоров\'я',
        'наука', 'спорт', 'технології',
    ]
}

CATEGORY_MAP = {
    'general': 'general',
    'business': 'business',
    'entertainment': 'entertainment',
    'health': 'health',
    'science': 'science',
    'sports': 'sports',
    'technology': 'technology'
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

CURRENCY_MAP = {
    'en': {
        'USD': 'US Dollar',
        'EUR': 'Euro',
        'GBP': 'British Pound',
        'PLN': 'Polish Zloty',
        'CHF': 'Swiss Franc',
        'CZK': 'Czech Koruna',
        'UAH': 'Ukrainian Hryvnia'
    },
    'uk': {
        'USD': 'долар США',
        'EUR': 'євро',
        'GBP': 'британський фунт',
        'PLN': 'польський злотий',
        'CHF': 'швейцарський франк',
        'CZK': 'чеська крона',
        'UAH': 'українська гривня'
    }
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
    - Retrieves news data based on country.
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
                                                                    language,
                                                                    'full')
    current_time = now.strftime('%H:%M')
    current_date = f"{translated_day}, {now.day} {translated_month} {now.year}"

    error_message = None
    weather_error_message = None
    default_city = 'Kyiv' if language == 'en' else 'Київ'
    city = request.GET.get('city', default_city)

    country = request.GET.get(
        'country', request.session.get('selected_country', 'us'
                                       if language == 'en' else 'ua')
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

    exchange_rates = fetch_exchange_rates(
        filter_currencies={'USD', 'EUR', 'PLN'}
    )

    news_data = {}
    for category in CATEGORY_MAP.keys():
        try:
            articles = fetch_news_by_category(category, country, trans)
            news_data[category] = articles
        except ValueError:
            news_data[category] = []

    request.session['news_data'] = news_data  # Store news data in session

    limited_news = {
        category: articles[:5] for category, articles in news_data.items()
    }

    context = {
        'translations': trans,
        'current_date': current_date,
        'current_time': current_time,
        'categories': CATEGORIES[language],
        'countries': COUNTRIES if language == 'en' else COUNTRIES_UA,
        'weather_data': weather_data,
        'exchange_rates': exchange_rates,
        'limited_news': limited_news,
        'selected_city': city,
        'selected_country': country,
        'selected_country_name': displayed_country_name,
        'genitive_country_name': genitive_country_name,
        'error_message': error_message,
        'weather_error_message': weather_error_message,
        'category_translations': {k: trans[k] for k in CATEGORY_MAP.keys()},
    }

    return render(request, 'newsapp/index.html', context)


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
        city_in_english, _, _ = get_city_and_country_info(city)
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


def fetch_weather_data(city, trans, lang='en'):
    cache_key = f'weather_data_{city}_{lang}'
    weather_data = cache.get(cache_key)

    try:
        city_in_english, country_code, _ = get_city_and_country_info(city)
    except ValueError:
        city_in_english = city  # Use original name if translation fails
    
    if not weather_data:
        url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={city_in_english}&lang={lang}&days=7"
        response = requests.get(url)
        data = response.json()

        if response.status_code != 200:
            error_msg = data.get('error', {}).get('message', 'Unknown error')
            if response.status_code == 401:
                raise ValueError(trans['invalid_key'])
            if response.status_code == 400:
                raise ValueError(trans['city_not_found'] % {'city': city})
            raise ValueError(trans['unable_to_retrieve_weather'] % {'error': error_msg})

        weather_data = {
            'current': {
                'temperature_c': round(data['current']['temp_c']),
                'temperature_f': round(data['current']['temp_f']),
                'feelslike_c': round(data['current']['feelslike_c']),
                'feelslike_f': round(data['current']['feelslike_f']),
                'condition': data['current']['condition']['text'],
                'icon_url': f"http:{data['current']['condition']['icon']}",
                'humidity': data['current']['humidity'],
                'wind_kph': round(data['current']['wind_kph']),
                'wind_mph': round(data['current']['wind_mph']),
                'pressure_mb': round(data['current']['pressure_mb']),
                'pressure_in': round(data['current']['pressure_in']),
                'visibility_km': data['current']['vis_km'],
                'visibility_miles': data['current']['vis_miles'],
                'uv_index': data['current']['uv'],
                'city': city_in_english,
                'country_code': country_code
            },
            'forecast': data['forecast']['forecastday']
        }
        
        cache.set(cache_key, weather_data, 3600)  # Cache for 1 hour

    return weather_data


def weather_page(request):
    language = request.GET.get('lang', request.session.get('language', 'en'))
    trans = translations.get(language, translations['en'])

    timezone_str = request.session.get('django_timezone', 'UTC')
    user_timezone = pytz.timezone(timezone_str)
    now = timezone.now().astimezone(user_timezone)

    translated_day, translated_month = get_translated_day_and_month(now, language, 'full')
    current_time = now.strftime('%H:%M')
    current_date = f"{translated_day}, {now.day} {translated_month} {now.year}"

    error_message = None
    default_city = 'Kyiv' if language == 'en' else 'Київ'
    city = request.GET.get('city', default_city)

    try:
        weather_data = fetch_weather_data(city, trans, language)
        city_in_english = weather_data['current']['city']
        country_code = weather_data['current']['country_code']
        country_name = get_country_name(country_code, 'uk') if language == 'uk' else get_country_name(country_code, 'en')
    except ValueError as ve:
        weather_data = None
        error_message = str(ve)
        country_name = None  # Set to None on error
    except requests.RequestException as e:
        error_message = trans['unable_to_retrieve_weather'] % {'error': str(e)}
        country_name = None  # Set to None on error

    context = {
        'translations': trans,
        'current_date': current_date,
        'current_time': current_time,
        'city': city,
        'weather_data': weather_data,
        'error_message': error_message,
        'language': language,
        'city_in_english': city_in_english,
        'country_name': country_name
    }

    request.session['language'] = language

    return render(request, 'newsapp/weather.html', context)


def fetch_exchange_rates(filter_currencies=None):
    """
    Fetch exchange rates data from PrivatBank API.
    - Retrieves the exchange rates for the required currencies.
    - Caches the result to improve performance.

    Returns:
    list: A list of exchange rates for the required currencies.
    """
    cache_key = 'exchange_rates'
    exchange_rates = cache.get(cache_key)

    if not exchange_rates:
        today = datetime.today().strftime('%d.%m.%Y')
        url = (
            'https://api.privatbank.ua/p24api/exchange_rates'
            f'?json&date={today}'
        )
        response = requests.get(url)
        data = response.json()

        exchange_rates = [
            rate for rate in data['exchangeRate']
            if 'currency' in rate and rate['currency'] != 'UAH'
        ]

        # Sort exchange rates by custom order
        custom_order = {
            'USD': 1, 'EUR': 2, 'GBP': 3, 'CHF': 4, 'PLN': 5, 'CZK': 6
        }
        exchange_rates.sort(key=lambda x: custom_order.get(x['currency'], 999))

        # Cache the exchange rates for 10 minutes (600 seconds)
        cache.set(cache_key, exchange_rates, 600)

    # Apply filtering if filter_currencies is provided
    if filter_currencies:
        exchange_rates = [
            rate for rate in exchange_rates
            if rate['currency'] in filter_currencies
        ]

    return exchange_rates


def exchange_rates_page(request):
    language = get_language(request)
    trans = translations.get(language, translations['en'])

    timezone_str = request.session.get('django_timezone', 'UTC')
    user_timezone = pytz.timezone(timezone_str)
    now = timezone.now().astimezone(user_timezone)

    translated_day, translated_month = get_translated_day_and_month(now,
                                                                    language,
                                                                    'full')
    current_time = now.strftime('%H:%M')
    current_date = f"{translated_day}, {now.day} {translated_month} {now.year}"

    # Filtered currencies
    filter_currencies = {'USD', 'EUR', 'GBP', 'PLN', 'CHF', 'CZK'}
    exchange_rates = fetch_exchange_rates(filter_currencies=filter_currencies)

    context = {
        'translations': trans,
        'current_date': current_date,
        'current_time': current_time,
        'exchange_rates': exchange_rates,
        'currency_names': CURRENCY_MAP[language],
        'converted_amount': request.session.get('converted_amount', '-'),
        'amount': request.session.get('amount', 0),
        'from_currency': request.session.get('from_currency', 'USD'),
        'to_currency': request.session.get('to_currency', 'EUR'),
    }

    return render(request, 'newsapp/exchange_rates.html', context)


def convert_currency_view(request):
    if request.method == 'POST':
        amount = float(request.POST.get('amount'))
        from_currency = request.POST.get('from_currency')
        to_currency = request.POST.get('to_currency')
        exchange_rates = fetch_exchange_rates(
            filter_currencies={'USD', 'EUR', 'GBP', 'CHF', 'PLN', 'CZK', 'UAH'}
        )

        conversion_result = convert_currency(
            amount, from_currency, to_currency, exchange_rates
        )

        # Save conversion result to session
        request.session['converted_amount'] = conversion_result
        request.session['amount'] = amount
        request.session['from_currency'] = from_currency
        request.session['to_currency'] = to_currency

        # Redirect to the same exchange rates page
        return redirect('newsapp:exchange_rates')

    return redirect('newsapp:exchange_rates')


def convert_currency(amount, from_currency, to_currency, exchange_rates):
    from_currency_buy_rate = None
    to_currency_sale_rate = None

    # Handling UAH as the base currency
    if from_currency == 'UAH':
        from_currency_buy_rate = 1
    if to_currency == 'UAH':
        to_currency_sale_rate = 1

    for rate in exchange_rates:
        if rate['currency'] == from_currency:
            from_currency_buy_rate = rate.get('purchaseRate',
                                              rate.get('saleRate'))
        if rate['currency'] == to_currency:
            to_currency_sale_rate = rate.get('saleRate',
                                             rate.get('purchaseRate'))

    if from_currency_buy_rate is None or to_currency_sale_rate is None:
        return None

    amount_in_uah = amount * from_currency_buy_rate
    converted_amount = amount_in_uah / to_currency_sale_rate
    return round(converted_amount, 2)


def news_by_category(request, category):
    language = get_language(request)
    trans = translations.get(language, translations['en'])

    timezone_str = request.session.get('django_timezone', 'UTC')
    user_timezone = pytz.timezone(timezone_str)
    now = timezone.now().astimezone(user_timezone)

    translated_day, translated_month = get_translated_day_and_month(now,
                                                                    language,
                                                                    'full')
    current_time = now.strftime('%H:%M')
    current_date = f"{translated_day}, {now.day} {translated_month} {now.year}"

    # Get the country from the request or session
    country = request.GET.get(
        'country', request.session.get('selected_country', 'us'
                                       if language == 'en' else 'ua')
    )

    # Update the session with the selected country
    request.session['selected_country'] = country

    displayed_country_name = (
        COUNTRIES_UA.get(country, 'Unknown') if language == 'uk'
        else COUNTRIES.get(country, 'Unknown')
    )
    genitive_country_name = (
        COUNTRIES_GENITIVE_UA.get(country, 'Unknown') if language == 'uk'
        else COUNTRIES.get(country, 'Unknown')
    )

    # Check if there are news in the session for the selected country,
    # if not, download the news
    news_data = request.session.get(f'news_data_{country}', {})
    if not news_data:
        for cat in CATEGORY_MAP.keys():
            try:
                articles = fetch_news_by_category(cat, country, trans)
                news_data[cat] = articles
            except ValueError:
                news_data[cat] = []
        request.session[f'news_data_{country}'] = news_data

    articles = news_data.get(category, [])

    category_titles = {
        'general': trans['general_title'],
        'business': trans['business_title'],
        'entertainment': trans['entertainment_title'],
        'health': trans['health_title'],
        'science': trans['science_title'],
        'sports': trans['sports_title'],
        'technology': trans['technology_title']
    }
    category_title = category_titles.get(category, trans['default_title'])

    context = {
        'translations': trans,
        'selected_country': country,
        'selected_country_name': displayed_country_name,
        'genitive_country_name': genitive_country_name,
        'countries': COUNTRIES if language == 'en' else COUNTRIES_UA,
        'categories': list(CATEGORY_MAP.keys()),
        'selected_category': category,
        'category_translations': {k: trans[k] for k in CATEGORY_MAP.keys()},
        'articles': articles,
        'current_time': current_time,
        'current_date': current_date,
        'category_title': category_title
    }

    return render(request, 'newsapp/category_news.html', context)
