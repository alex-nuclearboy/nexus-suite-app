from django.core.cache import cache

from datetime import datetime
import requests
import re
import os

# Define categories in different languages
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

# Map categories to their identifiers
CATEGORY_MAP = {
    'general': 'general',
    'business': 'business',
    'entertainment': 'entertainment',
    'health': 'health',
    'science': 'science',
    'sports': 'sports',
    'technology': 'technology'
}

NEWS_API_KEY = os.getenv('NEWS_API_KEY')


def fetch_news_by_category(category, country, transl):
    """
    Fetches news data from NewsAPI.

    This function retrieves news data for the specified category and country
    from the NewsAPI. The data is cached for 1 day to improve performance.
    If there's an error fetching the news, it raises a ValueError
    with an appropriate error message.

    Parameters:
    category (str): The news category.
    country (str): The country code.
    transl (dict): The translation dictionary.

    Returns:
    list: A list of news articles with titles, URLs, sources,
          and published time.

    Raises:
    ValueError: If there's an error fetching the news data.
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