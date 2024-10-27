from django.core.cache import cache

from asgiref.sync import sync_to_async
from datetime import datetime
import logging
import aiohttp
import os

from .location_utils import get_country_name_by_code, geocode_city
from .utils import generate_cache_key, get_translated_day_and_month

from .exceptions import (
    handle_weather_api_error,
    GeocodingError, UnableToRetrieveWeatherError,
    InvalidJSONResponseError, IncompleteWeatherDataError
)

logger = logging.getLogger(__name__)

WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')


async def fetch_weather_data(city, transl, language='en', data_type='both'):
    """
    Fetch weather data for a specified city.

    This function:
    - Generates a cache key based on the city, language, and data type.
    - Attempts to retrieve weather data from the cache.
    - Geocodes the city to get its latitude and longitude.
    - Fetches and processes weather data if not available in the cache.
    - Fetches and processes weather data from an external weather API if not
      available in the cache.
    - Stores the fetched weather data in the cache for future access.

    Parameters:
    city (str): Name of the city for which weather data is being fetched.
    transl (dict): Dictionary containing translations for error messages.
    language (str): Language code (default: 'en').
    data_type (str): Type of weather data to fetch:
                       'current' - for current weather data,
                       'forecast' - for 3-day forecast,
                       'both' - for both current and forecast data.

    Returns:
    dict: A dictionary containing the fetched weather data.

    Raises:
    GeocodingError: Raised if the geocoding service fails to locate the city.
    UnableToRetrieveWeatherError: Raised if there is an issue retrieving
                                  the weather data from the API.
    """
    cache_key = generate_cache_key('weather_data', city, language, data_type)
    weather_data = await sync_to_async(cache.get)(cache_key)

    default_value = 'N/A' if language == 'en' else 'н/д'

    try:
        geo_data = await geocode_city(city, transl=transl)
    except GeocodingError as e:
        raise UnableToRetrieveWeatherError(str(e))

    if not weather_data:
        try:
            weather_data = await fetch_and_process_weather_data(
                geo_data, transl, language, data_type, default_value
            )
            await sync_to_async(cache.set)(cache_key, weather_data, 3600)
        except Exception:
            raise UnableToRetrieveWeatherError(
                        transl['unable_to_retrieve_weather']
                    )

    return weather_data


async def fetch_and_process_weather_data(
        geo_data, transl, language, data_type, default_value
):
    """
    Fetch and process weather data from the weather API.

    This function:
    - Generates a cache key based on the geocoded city data, language,
      and data type.
    - Fetches current and/or forecast weather data from the API.
    - Processes the fetched weather data.
    - Processes the fetched data, handling translation of dates and error
      messages as needed.
    - Returns a structured dictionary with relevant weather information.

    Parameters:
    geo_data (dict): Geocoded data including city name, coordinates, etc.
    transl (dict): Dictionary containing translations for error messages.
    language (str): Language code for data localization.
    data_type (str): Type of weather data to fetch
                     ('current', 'forecast', or 'both').
    default_value (str): Default value for missing or unavailable data.

    Returns:
    dict: A dictionary containing processed weather data.

    Raises:
    InvalidJSONResponseError: Raised if the API response is not valid JSON.
    IncompleteWeatherDataError: Raised if the API response contains
                                incomplete weather data.
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
                    await handle_weather_api_error(response, transl)

                try:
                    data = await response.json()
                except ValueError:
                    raise InvalidJSONResponseError(
                        transl['invalid_JSON_response']
                    )
                except aiohttp.ContentTypeError:
                    raise UnableToRetrieveWeatherError(
                        transl['unable_to_retrieve_weather']
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
                    await handle_weather_api_error(response, transl)

                try:
                    data = await response.json()
                except ValueError:
                    raise InvalidJSONResponseError(
                        transl['invalid_JSON_response']
                    )
                except aiohttp.ContentTypeError:
                    raise UnableToRetrieveWeatherError(
                        transl['unable_to_retrieve_weather']
                    )

                forecast_days = data.get('forecast', {}).get('forecastday', [])
                if forecast_days:
                    today_forecast = forecast_days[0]
                    today_forecast['astro'] = {
                        'sunrise': today_forecast['astro'].get('sunrise',
                                                               default_value),
                        'sunset': today_forecast['astro'].get('sunset',
                                                              default_value),
                        'moon_phase': today_forecast['astro'].get('moon_phase',
                                                                  default_value
                                                                  ),
                    }
                    for day in forecast_days:
                        forecast_date_str = day.get('date')
                        if forecast_date_str:
                            forecast_date = datetime.strptime(
                                forecast_date_str, '%Y-%m-%d'
                            )
                            translated_day, translated_month = (
                                get_translated_day_and_month(forecast_date,
                                                             language)
                            )

                            day['forecast_date'] = {
                                'day': translated_day,
                                'date': forecast_date.day,
                                'month': translated_month,
                            }
                            day['max_temp_c'] = (
                                round(day.get('day', {}).get('maxtemp_c', 0))
                            )
                            day['max_temp_f'] = (
                                round(day.get('day', {}).get('maxtemp_f', 0))
                            )
                            day['min_temp_c'] = (
                                round(day.get('day', {}).get('mintemp_c', 0))
                            )
                            day['min_temp_f'] = (
                                round(day.get('day', {}).get('mintemp_f', 0))
                            )
                            day['condition'] = (
                                day.get('day', {}).get('condition',
                                                       default_value)
                            )

                            for hour in day.get('hour', []):
                                hour_time_str = hour.get('time')
                                if hour_time_str:
                                    hour['time'] = (
                                        datetime.strptime(hour_time_str,
                                                          '%Y-%m-%d %H:%M')
                                    )
                                    hour['temp_c'] = (
                                        round(hour.get('temp_c', 0))
                                    )
                                    hour['temp_f'] = (
                                        round(hour.get('temp_f', 0))
                                    )
                                    hour['wind_mps'] = (
                                        round(hour.get('wind_kph', 0) / 3.6)
                                    )
                                    hour['pressure_mb'] = (
                                        round(hour.get('pressure_mb', 0))
                                    )
                                    hour['pressure_mm'] = (
                                        round(hour.get('pressure_mb', 0)
                                              * 0.750062)
                                    )
                    weather_data['forecast'] = forecast_days

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
    Process current weather data to extract and format information.

    This function:
    - Extracts temperature, pressure, wind speed, visibility, and other details
      from the API response.
    - Handles any missing data using a provided default value.
    - Prepares the data for easy access and display.

    Parameters:
    data (dict): JSON data from the weather API response.
    default_value (str): Default value to use for missing or unavailable data.

    Returns:
    dict: Processed data dictionary with formatted current weather details.
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
