from django.core.cache import cache

from datetime import datetime, timedelta
import requests
import os
import re

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

NEWS_API_KEY = os.getenv('NEWS_API_KEY')


def get_translated_day_and_month(date_obj, language='en', format_type='full'):
    """
    Translate the day of the week and month name to the specified language.

    Parameters:
    dt (datetime): The datetime object to translate.
    language (str): The language code ('en' or 'uk').

    Returns:
    tuple: Translated day of the week and month name.
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
    try:
        day, month, time = date_string.split(' ', 2)
        month_index = int(month) - 1
        translated_month = MONTHS_TRANSLATIONS[format_type][lang][month_index]
        return f"{day} {translated_month} {time}"
    except (ValueError, IndexError):
        return date_string


def fetch_news_by_category(category, country, transl):
    """
    Fetch news data from NewsAPI.
    - Retrieves news data for the specified category and country.
    - Raises a ValueError if there is an error fetching news.

    Parameters:
    category (str): The news category.
    country (str): The country code.
    transl (dict): The translation dictionary.
    """

    cache_key = f'news_{category}_{country}'
    cached_news = cache.get(cache_key)

    if cached_news:
        return cached_news

    url = (
        f'https://newsapi.org/v2/top-headlines?country={country}'
        f'&category={category}&apiKey={NEWS_API_KEY}'
    )
    response = requests.get(url)
    data = response.json()
    if response.status_code != 200:
        error_msg = transl['error_fetching_news'].format(
            error=data.get('message', 'Unknown error')
        )
        raise ValueError(error_msg)

    articles = []
    for article in data['articles']:
        # Convert to datetime object
        published_at = datetime.fromisoformat(article['publishedAt'][:-1])

        title = article['title']
        source = article['source']['name']

        # Extract source from title if it exists at the end
        match = re.search(r' - ([^-]+)$', title)
        if match:
            title = title[:match.start()]
            source = match.group(1).strip()

        articles.append({
            'title': title,
            'url': article['url'],
            'source': source,
            'published_at': published_at.strftime('%d %m %H:%M')
        })

    # Cache the news data for 1 day
    cache.set(cache_key, articles, timeout=60*60*24)

    return articles
