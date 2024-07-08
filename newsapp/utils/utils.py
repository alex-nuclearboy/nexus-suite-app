import requests
from datetime import datetime
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
    'en': [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ],
    'uk': [
        'січня', 'лютого', 'березня', 'квітня', 'травня', 'червня',
        'липня', 'серпня', 'вересня', 'жовтня', 'листопада', 'грудня'
    ]
}

NEWS_API_KEY = os.getenv('NEWS_API_KEY')


def get_translated_day_and_month(dt, language='en'):
    """
    Translate the day of the week and month name to the specified language.

    Parameters:
    dt (datetime): The datetime object to translate.
    language (str): The language code ('en' or 'uk').

    Returns:
    tuple: Translated day of the week and month name.
    """
    day_name = DAYS_TRANSLATIONS[language][dt.weekday()]
    month_name = MONTHS_TRANSLATIONS[language][dt.month - 1]
    return day_name, month_name


def fetch_news_by_category(category, country, transl):
    """
    Fetch news data from NewsAPI.
    - Retrieves news data for the specified category and country.
    - Raises a ValueError if there is an error fetching news.

    Parameters:
    category (str): The news category.
    country (str): The country code.
    transl (dict): The translation dictionary.
    language (str): The language code.
    """
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
            'published_at': published_at
        })
    return articles
