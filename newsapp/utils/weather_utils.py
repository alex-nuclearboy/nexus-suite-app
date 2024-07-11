from django.core.cache import cache

from datetime import datetime
import requests
import os

from .location_utils import get_city_and_country_info

WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')


def fetch_weather_data(city, trans, lang='en', data_type='both'):
    """
    Fetch weather data from WeatherAPI.
    - Retrieves weather data for the specified city.
    - Uses the language parameter to get the data in the desired language.
    - Raises a ValueError if the city is not found.

    Parameters:
    city (str): The name of the city.
    trans (dict): The translation dictionary.
    lang (str): The language code.
    data_type (str): The type of data to fetch ('current', 'forecast', 'both').

    Returns:
    dict: The weather data.
    """
    cache_key = f'weather_data_{city}_{lang}_{data_type}'
    weather_data = cache.get(cache_key)

    try:
        city_en, _, country_name = get_city_and_country_info(city, lang)
    except ValueError:
        city_en = city  # Use original name if translation fails

    if not weather_data:
        urls = {
            'current': (
                f"http://api.weatherapi.com/v1/current.json"
                f"?key={WEATHER_API_KEY}&q={city_en}&lang={lang}"
            ),
            'forecast': (
                f"http://api.weatherapi.com/v1/forecast.json"
                f"?key={WEATHER_API_KEY}&q={city_en}&lang={lang}&days=3"
            )
        }

        weather_data = {}

        if data_type in ('current', 'both'):
            response = requests.get(urls['current'])
            data = response.json()
            if response.status_code != 200:
                error_msg = data.get('error', {}).get('message',
                                                      'Unknown error')
                if response.status_code == 401:
                    raise ValueError(trans['invalid_key'])
                if response.status_code == 400:
                    raise ValueError(trans['city_not_found'] % {'city': city})
                raise ValueError(
                    trans['unable_to_retrieve_weather'] % {'error': error_msg}
                )

            weather_data['current'] = {
                'temperature_c': round(data['current']['temp_c']),
                'temperature_f': round(data['current']['temp_f']),
                'feelslike_c': round(data['current']['feelslike_c']),
                'feelslike_f': round(data['current']['feelslike_f']),
                'dewpoint_c': round(data['current']['dewpoint_c']),
                'dewpoint_f': round(data['current']['dewpoint_f']),
                'condition': data['current']['condition']['text'],
                'icon_url': f"http:{data['current']['condition']['icon']}",
                'humidity': data['current']['humidity'],
                'wind_mps': round(data['current']['wind_kph'] / 3.6, 2),  # m/s
                'wind_kph': round(data['current']['wind_kph']),
                'wind_mph': round(data['current']['wind_mph']),
                'wind_dir': data['current']['wind_dir'],
                'pressure_mb': round(data['current']['pressure_mb']),
                'pressure_in': round(data['current']['pressure_in']),
                'pressure_mm': round(
                    data['current']['pressure_mb'] * 0.750062  # mmHg
                ),
                'visibility_km': data['current']['vis_km'],
                'visibility_miles': data['current']['vis_miles'],
                'uv_index': data['current']['uv'],
                'city': city_en,
                'country_name': country_name,
                'update_time': (
                    datetime.fromisoformat(data['current']['last_updated'])
                    .strftime('%H:%M')
                ),
            }

        if data_type in ('forecast', 'both'):
            response = requests.get(urls['forecast'])
            data = response.json()
            if response.status_code != 200:
                error_msg = data.get('error', {}).get('message',
                                                      'Unknown error')
                if response.status_code == 401:
                    raise ValueError(trans['invalid_key'])
                if response.status_code == 400:
                    raise ValueError(trans['city_not_found'] % {'city': city})
                raise ValueError(
                    trans['unable_to_retrieve_weather'] % {'error': error_msg}
                )
            weather_data['forecast'] = data['forecast']['forecastday']

        cache.set(cache_key, weather_data, 3600)  # Cache for 1 hour

    return weather_data
