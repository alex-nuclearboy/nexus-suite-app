from django.core.cache import cache
from django.http import JsonResponse
from django.utils import timezone

from datetime import datetime, timedelta
import pytz

DAYS_TRANSLATIONS = {
    'en': [
        'Monday', 'Tuesday', 'Wednesday', 'Thursday',
        'Friday', 'Saturday', 'Sunday'
    ],
    'uk': [
        'понеділок', 'вівторок', 'середа', 'четвер',
        'п\'ятниця', 'субота', 'неділя'
    ]
}

MONTHS_TRANSLATIONS = {
    'full': {
        'en': [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ],
        'uk': [
            'січня', 'лютого', 'березня', 'квітня', 'травня', 'червня',
            'липня', 'серпня', 'вересня', 'жовтня', 'листопада', 'грудня'
        ]
    },
    'abbr': {
        'en': [
            'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
        ],
        'uk': [
            'січ', 'лют', 'бер', 'кві', 'тра', 'чер',
            'лип', 'сер', 'вер', 'жов', 'лис', 'гру'
        ]
    }
}


def get_language(request):
    """
    Gets the language from the request or session.

    This function retrieves the language code from the GET parameters
    or the session. If no language is found, it defaults to English ('en').
    The retrieved language code is then stored in the session.

    Parameters:
    request (HttpRequest): The request object containing the GET parameters
                           and session.

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
    Sets the user's timezone based on the request.

    This function retrieves the 'timezone' parameter from the GET request,
    activates the timezone if it is valid, and stores the timezone in the
    user's session. It handles invalid timezone errors gracefully.

    Parameters:
    request (HttpRequest): The request containing the 'timezone' parameter
                           in the GET query string.

    Returns:
    JsonResponse: A response with a JSON object indicating the status
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


def get_translated_day_and_month(date_obj, language='en', format_type='full'):
    """
    Translates the day of the week and month name to the specified language.

    This function translates the day of the week and month name from a given
    datetime object to the specified language ('en' or 'uk').
    It caches the result until the end of the day to improve performance.

    Parameters:
    date_obj (datetime): The datetime object to translate.
    language (str): The language code ('en' or 'uk').
    format_type (str): The format type for the month ('full' or 'abbr').

    Returns:
    tuple: A tuple containing the translated day of the week and month name.
    """
    cache_key = (
        f"translated_day_month_{date_obj.strftime('%Y-%m-%d')}"
        f"_{language}_{format_type}"
    )
    cached_data = cache.get(cache_key)

    if cached_data:
        return cached_data

    day_name = DAYS_TRANSLATIONS[language][date_obj.weekday()]
    month_name = MONTHS_TRANSLATIONS[format_type][language][date_obj.month - 1]

    translated_data = (day_name, month_name)

    # Calculate seconds until the end of the day
    now = datetime.now()
    end_of_day = datetime.combine(now + timedelta(days=1), datetime.min.time())
    seconds_until_end_of_day = (end_of_day - now).seconds

    cache.set(cache_key, translated_data, seconds_until_end_of_day)

    return translated_data


def format_time(date_string, lang='en', format_type='abbr'):
    """
    Formats the date string to include translated month names.

    This function formats a date string to include the translated month name
    based on the specified language ('en' or 'uk') and format type
    ('full' or 'abbr').

    Parameters:
    date_string (str): The date string in the format 'DD MM HH:MM'.
    lang (str): The language code ('en' or 'uk').
    format_type (str): The format type for the month ('full' or 'abbr').

    Returns:
    str: The formatted date string with translated month name.
    """
    try:
        day, month, time = date_string.split(' ', 2)
        month_index = int(month) - 1
        translated_month = MONTHS_TRANSLATIONS[format_type][lang][month_index]
        return f"{day} {translated_month} {time}"
    except (ValueError, IndexError):
        return date_string
