from django.core.cache import cache

from opencage.geocoder import OpenCageGeocode
import pycountry
import requests
import os

GEOCODING_API_KEY = os.getenv('GEOCODING_API_KEY')

# Initialize geocoder
geocoder = OpenCageGeocode(GEOCODING_API_KEY)


def get_city_and_country_info(city_name, language='en'):
    """
    Retrieve city name in English, country code, and country name
    in specified language.

    Parameters:
    city_name (str): The city name to be translated.
    language (str): The language code ('en' or 'uk').

    Returns:
    tuple: The city name in English, the country code,
           and the country name in the specified language.
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
    Get the country name in the specified language.

    Parameters:
    country_code (str): The country code.
    language (str): The language code ('en' or 'uk').

    Returns:
    str: The country name in the specified language.
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
    Fetch the Ukrainian name of the country using Wikipedia's API.

    Parameters:
    country_name_en (str): The country name in English.

    Returns:
    str: The country name in Ukrainian.
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
