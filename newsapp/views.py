from django.shortcuts import render, redirect
from django.utils import timezone

import requests
import pytz

from .utils.translations import translations
from .utils.utils import (
    get_translated_day_and_month, get_language, set_timezone
)
from .utils.location_utils import (
    COUNTRIES, COUNTRIES_UA, COUNTRIES_GENITIVE_UA
)
from .utils.weather_utils import fetch_weather_data
from .utils.exchanger_utils import (
    CURRENCY_MAP, fetch_exchange_rates, convert_currency
)
from .utils.news_utils import CATEGORIES, CATEGORY_MAP, fetch_news_by_category


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

    set_timezone(request)

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
        weather_data = fetch_weather_data(
            city, trans, language, data_type='current'
        )
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


def weather_page(request):
    language = request.GET.get('lang', request.session.get('language', 'en'))
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
    default_city = 'Kyiv' if language == 'en' else 'Київ'
    city = request.GET.get('city', default_city)

    try:
        weather_data = fetch_weather_data(
            city, trans, language, data_type='both'
        )
        city_in_english = weather_data['current']['city']
        country_name = weather_data['current']['country_name']
        # country_name = (
        #     get_country_name(country_code, 'uk') if language == 'uk'
        #     else get_country_name(country_code, 'en')
        # )
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
