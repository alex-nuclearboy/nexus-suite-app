from django.core.cache import cache
from asgiref.sync import sync_to_async
import aiohttp
import os

from .location_utils import get_country_name_by_code, geocode_city
from .utils import generate_cache_key

from .exceptions import (
    CityNotFoundError, GeocodingServiceError, UnableToRetrieveWeatherError,
    InvalidAPIKeyError, InvalidJSONResponseError, IncompleteWeatherDataError
)

WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')


async def fetch_weather_data(city, transl, language='en', data_type='both'):
    """
    Fetch weather data for a specified city.

    This function:
    - Generates a cache key based on the city, language, and data type.
    - Attempts to retrieve weather data from the cache.
    - Geocodes the city to get its latitude and longitude.
    - Fetches and processes weather data if not available in the cache.
    - Stores the fetched weather data in the cache.

    Parameters:
    city (str): The name of the city.
    transl (dict): Dictionary containing translations for error messages.
    language (str): Language code (default: 'en').
    data_type (str): Type of weather data to fetch
                     ('current', 'forecast', or 'both').

    Returns:
    dict: The weather data.

    Raises:
    CityNotFoundError: If the city cannot be found.
    GeocodingServiceError: If there is an error with the geocoding service.
    UnableToRetrieveWeatherError: If the weather data cannot be retrieved.
    """
    cache_key = generate_cache_key('weather_data', city, language, data_type)
    weather_data = await sync_to_async(cache.get)(cache_key)

    default_value = 'N/A' if language == 'en' else 'н/д'

    try:
        geo_data = await geocode_city(city, transl=transl)
    except CityNotFoundError as e:
        raise CityNotFoundError(str(e))
    except GeocodingServiceError as e:
        print(f"Geocoding error: {str(e)}")
        raise UnableToRetrieveWeatherError(
            transl['unable_to_retrieve_weather'] % {'error': str(e)}
        )

    if not weather_data:
        weather_data = await fetch_and_process_weather_data(
            geo_data, transl, language, data_type, default_value
        )
        await sync_to_async(cache.set)(cache_key, weather_data, 3600)

    return weather_data


async def fetch_and_process_weather_data(
        geo_data, transl, language, data_type, default_value
):
    """
    Fetch and process weather data from the weather API.

    This function:
    - Generates a cache key based on the geocoded city data, language,
      and data type.
    - Attempts to retrieve weather data from the cache.
    - Constructs URLs for the weather API based on the data type.
    - Fetches current and/or forecast weather data from the API.
    - Processes the fetched weather data.
    - Stores the processed weather data in the cache.

    Parameters:
    geo_data (dict): Geocoded data including city name, coordinates, etc.
    transl (dict): Dictionary containing translations for error messages.
    language (str): Language code.
    data_type (str): Type of weather data to fetch
                     ('current', 'forecast', or 'both').
    default_value (str): Default value for missing data.

    Returns:
    dict: The processed weather data.

    Raises:
    InvalidJSONResponseError: If the weather API returns invalid JSON.
    IncompleteWeatherDataError: If the weather data is incomplete.
    """
    cache_key = generate_cache_key(
        'weather_data', geo_data['city_en'], language, data_type
    )
    cached_weather_data = await sync_to_async(cache.get)(cache_key)
    if cached_weather_data:
        return cached_weather_data

    urls = {
        'current': (
            f"http://api.weatherapi.com/v1/current.json"
            f"?key={WEATHER_API_KEY}&q={geo_data['lat']},{geo_data['lon']}"
            f"&lang={language}"
        ),
        'forecast': (
            f"http://api.weatherapi.com/v1/forecast.json"
            f"?key={WEATHER_API_KEY}&q={geo_data['lat']},{geo_data['lon']}"
            f"&lang={language}&days=3"
        )
    }

    weather_data = {}

    async with aiohttp.ClientSession() as session:
        if data_type in ('current', 'both'):
            async with session.get(urls['current']) as response:

                # Check if response status is not 200 and handle errors
                if response.status != 200:
                    await handle_weather_api_error(
                        response, transl, geo_data['city_en']
                    )

                try:
                    data = await response.json()
                except ValueError:
                    raise InvalidJSONResponseError(
                        transl['invalid_JSON_response']
                    )

                if 'current' not in data or not data['current']:
                    raise IncompleteWeatherDataError(
                        transl['incomplete_weather_data']
                    )

                weather_data.update(
                    process_current_weather_data(data, default_value)
                )

        if data_type in ('forecast', 'both'):
            async with session.get(urls['forecast']) as response:
                if response.status != 200:
                    await handle_weather_api_error(
                        response, transl, geo_data['city_en']
                    )

                try:
                    data = await response.json()
                except ValueError:
                    raise InvalidJSONResponseError(
                        transl['invalid_JSON_response']
                    )

                weather_data['forecast'] = (
                    data.get('forecast', {}).get('forecastday', [])
                )
                for day in weather_data['forecast']:
                    day['astro']['sunrise'] = (
                        day['astro'].get('sunrise', default_value)
                    )
                    day['astro']['sunset'] = (
                        day['astro'].get('sunset', default_value)
                    )
                    day['astro']['moon_phase'] = (
                        day['astro'].get('moon_phase', default_value)
                    )

        weather_data.update({
            'geo_city': geo_data['city_en'],
            'geo_region': geo_data['region'],
            'geo_country': geo_data['country_name'],
            'country_code': geo_data['country_code'],
            'country': get_country_name_by_code(geo_data['country_code'])
        })

    await sync_to_async(cache.set)(cache_key, weather_data, 3600)
    return weather_data


def process_current_weather_data(data, default_value):
    """
    Process current weather data.

    This function:
    - Extracts and processes relevant weather data from the API response.
    - Handles missing data by using a default value.
    - Formats the extracted weather data.

    Parameters:
    data (dict): The weather data from the API.
    default_value (str): Default value for missing data.

    Returns:
    dict: The processed current weather data.
    """
    api_city = data['location'].get('name', default_value)
    api_region = data['location'].get('region', default_value)
    api_country = data['location'].get('country', default_value)

    current_data = {
        'api_city': api_city,
        'api_region': api_region,
        'api_country': api_country,
        'tz_id': data['location'].get('tz_id', 'UTC'),
        'current': {
            'temperature_c': round(data['current'].get('temp_c', 0)),
            'temperature_f': round(data['current'].get('temp_f', 0)),
            'feelslike_c': round(data['current'].get('feelslike_c', 0)),
            'feelslike_f': round(data['current'].get('feelslike_f', 0)),
            'dewpoint_c': round(data['current'].get('dewpoint_c', 0)),
            'dewpoint_f': round(data['current'].get('dewpoint_f', 0)),
            'condition': (
                data['current']['condition'].get('text', default_value)
            ),
            'icon_url': f"http:{data['current']['condition'].get('icon', '')}",
            'humidity': data['current'].get('humidity', 0),
            'wind_mps': round(data['current'].get('wind_kph', 0) / 3.6),  # m/s
            'wind_kph': round(data['current'].get('wind_kph', 0)),
            'wind_mph': round(data['current'].get('wind_mph', 0)),
            'wind_dir': data['current'].get('wind_dir', 'Unknown'),
            'pressure_mb': round(data['current'].get('pressure_mb', 0)),
            'pressure_in': round(data['current'].get('pressure_in', 0)),
            'pressure_mm': (
                round(data['current'].get('pressure_mb', 0) * 0.750062)
            ),  # mmHg
            'visibility_km': data['current'].get('vis_km', 0),
            'visibility_miles': data['current'].get('vis_miles', 0),
            'uv_index': data['current'].get('uv', 0),
            'update_time': data['current'].get(
                'last_updated', '1970-01-01 00:00:00'
            ),
            'localtime': data['location'].get(
                'localtime', '1970-01-01 00:00:00'
            ),
        }
    }

    return current_data


async def handle_weather_api_error(response, trans, city):
    """
    Handles errors from the weather API response.

    This function:
    - Reads the error message from the API response.
    - Raises appropriate exceptions based on the response status code.

    Parameters:
    response (aiohttp.ClientResponse): The HTTP response object.
    trans (dict): Dictionary containing translations for error messages.
    city (str): The city name.

    Raises:
    InvalidAPIKeyError: If the API key is invalid.
    CityNotFoundError: If the city is not found.
    UnableToRetrieveWeatherError: For other weather API errors.
    """
    error_msg = await response.text()
    print("Weather API error response:", error_msg)
    if response.status == 401:
        raise InvalidAPIKeyError(trans['invalid_key'])
    if response.status == 400:
        raise CityNotFoundError(trans['city_not_found'] % {'city': city})
    raise UnableToRetrieveWeatherError(
        trans['unable_to_retrieve_weather'] % {'error': error_msg}
    )
