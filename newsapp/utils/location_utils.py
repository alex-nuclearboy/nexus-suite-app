from django.core.cache import cache

from opencage.geocoder import OpenCageGeocode
import pycountry
import requests
import os

# API key for OpenCage Geocoding
GEOCODING_API_KEY = os.getenv('GEOCODING_API_KEY')

# Initialize geocoder
geocoder = OpenCageGeocode(GEOCODING_API_KEY)

# Country name mappings for different languages
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


def get_city_and_country_info(city_name, language='en'):
    """
    Retrieves city name in English, country code, and country name
    in the specified language.

    This function uses the OpenCage Geocoding API to fetch the city name
    in English, the corresponding country code, and the country name
    in the specified language.
    The data is cached for 1 hour to improve performance.

    Parameters:
    city_name (str): The name of the city to be translated.
    language (str): The language code ('en' or 'uk'). Defaults to 'en'.

    Returns:
    tuple: A tuple containing the city name in English, the country code,
    and the country name in the specified language.

    Raises:
    ValueError: If the city name could not be geocoded.
    """
    cache_key = f'city_country_info_{city_name}_{language}'
    city_country_info = cache.get(cache_key)

    if not city_country_info:
        # Fetch city and country info using OpenCage Geocoding API
        results = geocoder.geocode(city_name, language='en')
        if results and len(results):
            city = results[0]['components'].get('city') or \
                   results[0]['components'].get('town') or \
                   results[0]['components'].get('village')
            country_code = results[0]['components'].get('country_code').upper()

            # Fetch country name in specified language
            country_name = get_country_name(country_code, language)

            city_country_info = (city, country_code, country_name)
            cache.set(cache_key, city_country_info, 3600)  # Cache for 1 hour
        else:
            raise ValueError(f"Could not geocode city name: {city_name}")
    return city_country_info


def get_country_name(country_code, language):
    """
    Gets the country name in the specified language.

    This function uses the pycountry library to fetch the country name
    in the specified language. If the language is Ukrainian, it uses
    Wikipedia's API to fetch the Ukrainian name of the country.

    Parameters:
    country_code (str): The country code (ISO 3166-1 alpha-2).
    language (str): The language code ('en' or 'uk').

    Returns:
    str: The country name in the specified language.

    Raises:
    ValueError: If the country name could not be fetched.
    """
    country = pycountry.countries.get(alpha_2=country_code)

    if not country:
        return None

    if language == 'uk':
        # Use Wikipedia's API to get the Ukrainian name
        return get_country_name_uk(country.name)
    return country.name


def get_country_name_uk(country_name_en):
    """
    Fetches the Ukrainian name of the country using Wikipedia's API.

    This function uses Wikipedia's API to fetch the Ukrainian name of the
    country based on its English name. If the Ukrainian name is not found,
    it defaults to the English name.

    Parameters:
    country_name_en (str): The country name in English.

    Returns:
    str: The country name in Ukrainian.

    Raises:
    Exception: If there is an error fetching the country name.
    """
    try:
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "titles": country_name_en,
            "prop": "langlinks",
            "lllang": "uk",
            "format": "json"
        }
        response = requests.get(url, params=params)
        data = response.json()

        pages = data["query"]["pages"]
        for page_id, page in pages.items():
            if "langlinks" in page:
                langlinks = page["langlinks"]
                for link in langlinks:
                    if link["lang"] == "uk":
                        return link["*"]
        # Default to English name if Ukrainian name not found
        return country_name_en
    except Exception as e:
        print(f"Error fetching country name for {country_name_en}: {e}")
        return country_name_en  # Default to English name on error
