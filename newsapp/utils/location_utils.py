from django.core.cache import cache
from django.conf import settings

from asgiref.sync import sync_to_async
import aiohttp
import aiofiles
import pycountry
import json
import os
import re

from .utils import generate_cache_key
from .exceptions import (
    GeocodingServiceError,
    CityNotFoundError,
    WikipediaAPIError,
    JSONDecodingError,
    NameNotFoundError
)

# API key for OpenCage Geocoding
GEOCODING_API_KEY = os.getenv('GEOCODING_API_KEY')

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


async def geocode_city(city_name, country_code=None, transl=None):
    """
    Geocode the city name to get latitude and longitude.

    This function:
    - Generates a cache key based on the city name.
    - Attempts to retrieve geocoded data from the cache.
    - Queries the OpenCage Geocoding API to get the city's coordinates.
    - Processes the API response to extract relevant location data.
    - Stores the geocoded data in the cache.

    Parameters:
    city_name (str): The name of the city to geocode.
    country_code (str): The ISO 3166-1 alpha-2 country code (optional).
    transl (dict): Dictionary containing translations for error messages.

    Returns:
    dict: A dictionary containing the city name in English, country code,
          country name, region, and coordinates (latitude, longitude).

    Raises:
    CityNotFoundError: If the city cannot be found.
    GeocodingServiceError: For general geocoding service errors.
    """
    cache_key = generate_cache_key('geocode', city_name)
    cached_data = await sync_to_async(cache.get)(cache_key)
    if cached_data:
        return cached_data

    query = f"{city_name}, {country_code}" if country_code else city_name

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.opencagedata.com/geocode/v1/json?q={query}"
                f"&key={GEOCODING_API_KEY}"
            ) as response:
                if response.status != 200:
                    raise GeocodingServiceError(
                        transl['geocoding_service_error'] %
                        {'error': response.reason}
                    )
                result = await response.json()

    except aiohttp.ClientError as e:
        print(f"Geocoding service error: {e}")
        raise GeocodingServiceError(
            transl['geocoding_service_error'] % {'error': str(e)}
        )

    if result and len(result['results']):
        components = result['results'][0]['components']
        city_en = (
            components.get('city') or
            components.get('town') or
            components.get('village') or
            components.get('state_district')
        )
        country_code = components.get('country_code', '').upper()
        country_name = components.get('country')
        region = (
            components.get('state') or
            components.get('province') or
            components.get('region')
        )
        lat = result['results'][0]['geometry']['lat']
        lon = result['results'][0]['geometry']['lng']

        # Ensure Kyiv region is set correctly
        if city_en and city_en.lower() == 'kyiv':
            region = 'Kyiv Oblast'

        geo_data = {
            'city_en': city_en,
            'country_code': country_code,
            'country_name': country_name,
            'region': region,
            'lat': lat,
            'lon': lon
        }

        await sync_to_async(cache.set)(cache_key, geo_data, 3600)
        return geo_data

    raise CityNotFoundError(transl['could_not_geocode'] % {'city': city_name})


def get_country_name_by_code(country_code):
    """
    Retrieve the country name using the country code.

    This function:
    - Uses the pycountry library to get the country name corresponding
      to the provided country code.

    Parameters:
    country_code (str): The ISO 3166-1 alpha-2 country code.

    Returns:
    str: The country name in English.
    """
    try:
        country = pycountry.countries.get(alpha_2=country_code)
        return country.name
    except AttributeError:
        return 'Unknown'


async def translate_to_ukrainian(name, transl, source='country'):
    """
    Translate the name of a country or region to Ukrainian
    using Wikipedia's API.

    This function:
    - Queries the Wikipedia API to get the Ukrainian translation
      of the provided name.
    - Processes the API response to extract the translated name.
    - Handles errors related to the API request and response processing.

    Parameters:
    name (str): The name of the country or region in English.
    transl (dict): Dictionary containing translations for error messages.
    source (str): Indicates whether the name is a 'country' or 'region'
                  (default to 'country').

    Returns:
    str: The translated name in Ukrainian.

    Raises:
    WikipediaAPIError: If there is an error with the Wikipedia API request.
    JSONDecodingError: If there is an error decoding the JSON response.
    NameNotFoundError: If the name is not found in the Wikipedia API response.
    """
    if not name:
        raise NameNotFoundError(
            transl[f'{source}_name_not_found'] % {'name': name}
        )

    try:
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "titles": name,
            "prop": "langlinks",
            "lllang": "uk",
            "format": "json"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

    except aiohttp.ClientError as e:
        print(f"Wikipedia API error: {e}")
        raise WikipediaAPIError(
            transl['wikipedia_api_error'] % {'error': str(e)}
        )
    except ValueError:
        raise JSONDecodingError(transl['json_decoding_error'])

    pages = data.get("query", {}).get("pages", {})
    for page_id, page in pages.items():
        if "langlinks" in page:
            langlinks = page["langlinks"]
            for link in langlinks:
                if link["lang"] == "uk":
                    translated_name = link["*"]
                    # Remove text in parentheses and extra phrases
                    clean_name = re.sub(r'\s*\(.*?\)', '', translated_name)
                    clean_name = re.sub(r',.*', '', clean_name)
                    return clean_name.strip()

    raise NameNotFoundError(
        transl[f'{source}_name_not_found'] % {'name': name}
    )


async def get_translated_name(
        name, name_alternatives, transl, source='country'
):
    """
    Try to translate the name to Ukrainian using various alternatives.

    This function:
    - Generates a cache key based on the name and source.
    - Attempts to retrieve the translated name from the cache.
    - Calls the translate_to_ukrainian function to get the translation.
    - Tries alternative names if the initial translation fails.
    - Stores the translated name in the cache.

    Parameters:
    name (str): The original name.
    name_alternatives (list): List of alternative names to try for translation.
    transl (dict): Dictionary containing translations for error messages.
    source (str): Indicates whether the name is a 'country' or 'region'
                  (default to 'country').

    Returns:
    str: The translated name in Ukrainian.
    """
    cache_key = generate_cache_key('translate', name, source)
    cached_translation = await sync_to_async(cache.get)(cache_key)
    if cached_translation:
        return cached_translation

    try:
        return await translate_to_ukrainian(name, transl, source)
    except NameNotFoundError:
        for alt_name in name_alternatives:
            try:
                return await translate_to_ukrainian(alt_name, transl, source)
            except NameNotFoundError:
                continue
        return name  # Default to the original name if translation fails


async def process_city_info(
        city, geo_city, country_code, country_name_en, region_en,
        api_country, api_region, language, transl
):
    """
    Process city information based on the language and JSON file
    for Ukrainian language.

    This function:
    - Reads city information from a JSON file for Ukrainian translations.
    - Translates the city, region, and country names if the language
      is Ukrainian.
    - Constructs the weather_in_text based on the language.

    Parameters:
    city (str): The name of the city.
    country_code (str): The ISO 3166-1 alpha-2 country code.
    country_name_en (str): The English name of the country.
    region_en (str): The English name of the region.
    api_country (str): The country name returned by the weather API.
    api_region (str): The region name returned by the weather API.
    language (str): The language code.
    transl (dict): Dictionary containing translations for error messages.

    Returns:
    tuple: A tuple containing the processed city name, region, country name,
           and weather_in_text.
    """
    if language == 'uk':
        json_file_path = os.path.join(
            settings.BASE_DIR, 'newsapp', 'data',
            'cities_of_ukraine_with_final_locative_and_region.json'
        )
        async with aiofiles.open(json_file_path, 'r', encoding='utf-8') as fh:
            cities_data = json.loads(await fh.read())
            city_info = next((item for item in cities_data['cities']
                              if item["name"].lower() == city.lower()), None)

        if city_info:
            translated_city = city_info['locative']
            region = city_info['region']
            weather_in_text = 'Погода у'
        else:
            translated_city = await get_translated_name(
                geo_city, [geo_city], transl, source='city'
            )
            region = await get_translated_name(
                region_en,
                [region_en, api_region],
                transl,
                source='region'
            )
            weather_in_text = 'Погода у місті'

        country_name = await get_translated_name(
            country_name_en, [get_country_name_by_code(country_code),
                              country_name_en, api_country], transl
        )

        # Check if the input city name matches the translated city name
        if translated_city and city.lower() != translated_city.lower():
            city = translated_city

    else:
        region = region_en
        country_name = country_name_en
        weather_in_text = transl['weather_in']

    return city, region, country_name, weather_in_text
