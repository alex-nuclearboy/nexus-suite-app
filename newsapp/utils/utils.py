from django.core.cache import cache
from django.http import JsonResponse
from django.utils import timezone

from urllib.parse import quote
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


def safe_cache_key(key):
    """
    Encodes a given key to ensure it is safe for use in a cache.

    Parameters:
    key (str): The key to be encoded.

    Returns:
    str: The encoded key.
    """
    return quote(key, safe='')


def generate_cache_key(*args):
    """
    Generate a safe cache key by encoding its parts.

    Parameters:
    *args: The parts of the cache key to be joined and encoded.

    Returns:
    str: The generated safe cache key.
    """
    return ':'.join([safe_cache_key(str(arg)) for arg in args])


def get_update_times(weather_data, user_timezone, transl):
    """
    Get the update times in local and user timezones.

    Parameters:
    weather_data (dict): Dictionary containing weather data.
    user_timezone (timezone): User's timezone object.
    transl (dict): Dictionary containing translations for error messages.

    Returns:
    tuple: A tuple containing formatted local update time and user update time.
    """
    try:
        if (
            weather_data and 'current' in weather_data
            and 'update_time' in weather_data['current']
        ):
            # Define local timezone
            local_timezone = pytz.timezone(weather_data['tz_id'])

            # Get local update time and convert to datetime
            local_update_time_str = weather_data['current']['update_time']
            local_update_time = datetime.strptime(
                local_update_time_str, '%Y-%m-%d %H:%M'
            )

            # Assign timezone to local update time
            local_update_time = local_timezone.localize(local_update_time)

            # Convert local update time to user's timezone
            user_update_time = local_update_time.astimezone(user_timezone)

            formatted_local_update_time = local_update_time.strftime('%H:%M')
            formatted_user_update_time = user_update_time.strftime('%H:%M')
        else:
            raise ValueError("Missing required weather data for update times")

        return formatted_local_update_time, formatted_user_update_time
    except Exception as e:
        print(f"Error getting update times: {e}")
        return 'N/A', 'N/A'
