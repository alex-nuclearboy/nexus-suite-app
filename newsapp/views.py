from django.views import View
from django.core.cache import cache
from django.shortcuts import render, redirect
from django.utils import timezone

from asgiref.sync import sync_to_async
import logging
import pytz

from .utils.translations import translations
from .utils.utils import (
    get_translated_day_and_month, get_language,
    set_timezone, get_update_times
)
from .utils.location_utils import (
    COUNTRIES, COUNTRIES_UA, COUNTRIES_GENITIVE_UA
)
from .utils.weather_utils import fetch_weather_data
from .utils.exchanger_utils import (
    CURRENCY_MAP, fetch_exchange_rates, convert_currency
)
from .utils.news_utils import CATEGORY_MAP, fetch_news_by_category
from .utils.location_utils import process_city_info
from .utils.exceptions import (APIError, UnableToRetrieveWeatherError)

logger = logging.getLogger(__name__)


class BaseView(View):
    """
    Base class view that includes common context setup, like date, time,
    and translations, to be used across various views.
    """
    def get_user(self, request):
        """Return the current user."""
        return request.user

    @sync_to_async
    def is_authenticated(self, request):
        """Check if the user is authenticated."""
        return request.user.is_authenticated

    def get_avatar_url(self, user):
        """
        Retrieves the avatar URL for a user.
        """
        if (
            user.is_authenticated
                and hasattr(user, 'profile')
                and user.profile.avatar
        ):
            return user.profile.avatar.url
        return None

    async def get_common_context(self, request):
        """
        Forms and returns a common context dictionary for all views.

        Parameters:
        request: User's session request object containing session data.

        Returns:
        dict: Dictionary with general data such as language, timezone,
              current date and time, and translations.
        """
        language = await sync_to_async(get_language)(request)
        transl = translations.get(language, translations['en'])

        await sync_to_async(set_timezone)(request)

        # Get user's timezone and current time
        timezone_str = (
            await sync_to_async(request.session.get)('django_timezone', 'UTC')
        )
        user_timezone = pytz.timezone(timezone_str)
        now = timezone.now().astimezone(user_timezone)

        # Translate the date and time
        translated_day, translated_month = (
            await sync_to_async(get_translated_day_and_month)(
                now, language, 'full'
            )
        )
        current_time = now.strftime('%H:%M')
        current_date = (
            f"{translated_day}, {now.day} {translated_month} {now.year}"
        )

        # Retrieve user's avatar URL
        user = await sync_to_async(self.get_user)(request)
        avatar_url = await sync_to_async(self.get_avatar_url)(request.user)

        return {
            'language': language,
            'translations': transl,
            'current_date': current_date,
            'current_time': current_time,
            'user_timezone': user_timezone,
            'user': user,
            'avatar_url': avatar_url,
        }


class MainView(BaseView):
    """
    Main view to handle the homepage, displaying weather,
    exchange rates, and news.
    """

    async def get(self, request):
        """
        Handles the GET request for rendering the homepage with weather,
        exchange rates, and news data.

        Parameters:
        request: User's session request object containing session data.

        Returns:
        HttpResponse: Rendered homepage with the fetched context.
        """
        context = await self.get_common_context(request)
        language = context['language']
        transl = context['translations']
        user_timezone = context['user_timezone']

        weather_error_message = None
        exchange_rate_error_message = None

        default_city = 'Kyiv' if language == 'en' else 'Київ'
        current_city = request.session.get('selected_city', default_city)

        # Update city to default when language is switched
        if 'language' in request.GET:
            request.session['selected_city'] = default_city
            city = default_city
        else:
            city = request.GET.get('city', current_city)
            if city != current_city:
                await sync_to_async(request.session.__setitem__)(
                    'selected_city', city
                )

        country = request.GET.get(
            'country', await sync_to_async(request.session.get)(
                'selected_country', 'us' if language == 'en' else 'ua'
            )
        )

        if language == 'en':
            await sync_to_async(request.session.__setitem__)(
                'selected_country', 'us'
            )
            country = 'us'
        else:
            await sync_to_async(request.session.__setitem__)(
                'selected_country', 'ua'
            )
            country = 'ua'

        displayed_country_name = (
            COUNTRIES_UA.get(country, 'Unknown') if language == 'uk'
            else COUNTRIES.get(country, 'Unknown')
        )
        genitive_country_name = (
            COUNTRIES_GENITIVE_UA.get(country, 'Unknown') if language == 'uk'
            else COUNTRIES.get(country, 'Unknown')
        )

        # Fetch weather data
        try:
            weather_data = await fetch_weather_data(
                city, transl, language, data_type='current'
            )
        except UnableToRetrieveWeatherError as e:
            weather_error_message = (
                transl['could_not_geocode'] % {'city': city}
            )
            logger.error(f"Weather retrieval error for {city}: {str(e)}")
            weather_data = None

        if weather_data is None:
            await sync_to_async(request.session.__setitem__)('selected_city',
                                                             default_city)

        # Fetch exchange rates
        try:
            exchange_rates = await fetch_exchange_rates(
                filter_currencies={'USD', 'EUR', 'PLN'}
            )
        except APIError as e:
            logger.error(f"Error fetching exchange rates: {str(e)}")
            exchange_rates = []
            exchange_rate_error_message = transl[
                'unable_to_fetch_exchange_rates'
            ]

        # Fetch news articles for the main page
        try:
            general_news = await fetch_news_by_category('general',
                                                        country, transl)
            articles = general_news[:10]
        except APIError as e:
            logger.error(f"Error fetching general news: {str(e)}")
            context['error_message'] = transl['unable_to_fetch_news']
            articles = []

        formatted_local_update_time, formatted_user_update_time = \
            get_update_times(weather_data, user_timezone, transl)

        context.update({
            'weather_error_message': weather_error_message,
            'weather_data': weather_data,
            'exchange_rates': exchange_rates,
            'articles': articles,
            'all_news_link': True,
            'selected_city': city,
            'selected_country': country,
            'selected_country_name': displayed_country_name,
            'genitive_country_name': genitive_country_name,
            'category_translations': {
                k: transl[k] for k in CATEGORY_MAP.keys()
            },
            'local_update_time': formatted_local_update_time,
            'user_update_time': formatted_user_update_time,
            'countries': COUNTRIES if language == 'en' else COUNTRIES_UA,
            'exchange_rate_error_message': exchange_rate_error_message,
            'is_authenticated': await self.is_authenticated(request),
        })

        return render(request, 'newsapp/index.html', context)


class WeatherView(BaseView):
    """
    View to handle weather data requests for a specific location.
    """

    async def get(self, request):
        """
        Handles the GET request for fetching and displaying
        detailed weather data.

        Parameters:
        request: User's request containing parameters like location.

        Returns:
        HttpResponse: Rendered page with detailed weather information.
        """
        context = await self.get_common_context(request)
        language = context['language']
        transl = context['translations']
        user_timezone = context['user_timezone']

        error_message = None
        default_city = 'Kyiv' if language == 'en' else 'Київ'
        city = request.session.get('selected_city', default_city)
        if 'city' in request.GET:
            city = request.GET['city']
            await sync_to_async(request.session.__setitem__)('selected_city',
                                                             city)

        try:
            weather_data = await fetch_weather_data(
                city, transl, language, data_type='both'
            )
            city, region, country_name, weather_in_text = (
                await process_city_info(
                    city,
                    weather_data['geo_city'],
                    weather_data['country_code'],
                    weather_data['geo_country'],
                    weather_data['geo_region'],
                    weather_data['api_country'],
                    weather_data['api_region'],
                    language,
                    transl
                )
            )

            formatted_local_update_time, formatted_user_update_time = \
                get_update_times(weather_data, user_timezone, transl)

        except UnableToRetrieveWeatherError:
            error_message = transl['could_not_geocode'] % {'city': city}
            weather_data = None
            country_name = None
            region = None
            weather_in_text = transl['weather_in']
            formatted_local_update_time = 'N/A'
            formatted_user_update_time = 'N/A'

            # Set default city if weather data cannot be retrieved
            await sync_to_async(request.session.__setitem__)('selected_city',
                                                             default_city)

        context.update({
            'error_message': error_message,
            'weather_data': weather_data,
            'city': city,
            'country_name': country_name,
            'region': region,
            'weather_in_text': weather_in_text,
            'local_update_time': formatted_local_update_time,
            'user_update_time': formatted_user_update_time,
        })

        await sync_to_async(request.session.__setitem__)('language', language)

        return render(request, 'newsapp/weather.html', context)


class ExchangeRatesView(BaseView):
    """
    View to handle requests for displaying current exchange rates.
    """

    async def get(self, request):
        """
        Handles the GET request for showing updated exchange rates.

        Parameters:
        request: User's request object.

        Returns:
        HttpResponse: Rendered page with current exchange rate information.
        """
        context = await self.get_common_context(request)
        language = context['language']
        transl = context['translations']

        filter_currencies = {'USD', 'EUR', 'GBP', 'PLN', 'CHF', 'CZK'}

        try:
            exchange_rates = await fetch_exchange_rates(
                filter_currencies=filter_currencies
            )
            error_message = None
        except APIError as e:
            logger.error(f"Error fetching exchange rates: {str(e)}")
            exchange_rates = []
            error_message = transl['unable_to_fetch_exchange_rates']

        converted_amount = request.session.pop('converted_amount', '-')
        amount = request.session.pop('amount', 0)
        from_currency = request.session.pop('from_currency', 'USD')
        to_currency = request.session.pop('to_currency', 'UAH')
        conversion_error_message = request.session.pop(
            'conversion_error_message', None
        )

        context.update({
            'exchange_rates': exchange_rates,
            'currency_names': CURRENCY_MAP[language],
            'amount': amount,
            'converted_amount': converted_amount,
            'from_currency': from_currency,
            'to_currency': to_currency,
            'error_message': error_message,
            'conversion_error_message': conversion_error_message,
        })

        return render(request, 'newsapp/exchange_rates.html', context)


class ConvertCurrencyView(BaseView):
    """
    View to handle currency conversion requests.
    """

    async def post(self, request):
        """
        Handles the GET request for converting one currency to another.

        Parameters:
        request: User's request containing 'from_currency', 'to_currency',
                 and 'amount'.

        Returns:
        HttpResponse: Rendered page with converted currency value.
        """
        context = await self.get_common_context(request)
        transl = context['translations']
        if request.method == 'POST':
            amount = float(request.POST.get('amount'))
            from_currency = request.POST.get('from_currency')
            to_currency = request.POST.get('to_currency')
            exchange_rates = await fetch_exchange_rates(
                filter_currencies={
                    'USD', 'EUR', 'GBP', 'CHF', 'PLN', 'CZK', 'UAH'
                }
            )

            conversion_result, error_message = await convert_currency(
                amount, from_currency, to_currency, exchange_rates, transl
            )

            if error_message:
                await sync_to_async(request.session.__setitem__)(
                    'conversion_error_message', error_message
                )
                await sync_to_async(request.session.__setitem__)(
                    'amount', amount
                )
                await sync_to_async(request.session.__setitem__)(
                    'from_currency', from_currency
                )
                await sync_to_async(request.session.__setitem__)(
                    'to_currency', to_currency
                )
                return redirect('newsapp:exchange_rates')

            # Save conversion result to session
            await sync_to_async(request.session.__setitem__)(
                'converted_amount', conversion_result
            )
            await sync_to_async(request.session.__setitem__)(
                'amount', amount
            )
            await sync_to_async(request.session.__setitem__)(
                'from_currency', from_currency
            )
            await sync_to_async(request.session.__setitem__)(
                'to_currency', to_currency
            )

        return redirect('newsapp:exchange_rates')


class NewsView(BaseView):
    """
    View to handle requests for displaying news articles by category.
    """

    async def get(self, request, category):
        """
        Handles the GET request for fetching and displaying news articles
        in a specific category.

        Parameters:
        request: User's request with 'category' parameter for filtering news.

        Returns:
        HttpResponse: Rendered page with a list of news articles.
        """
        context = await self.get_common_context(request)
        language = context['language']
        transl = context['translations']

        # Get the country from the request or session
        country = request.GET.get(
            'country', await sync_to_async(request.session.get)(
                'selected_country', 'us' if language == 'en' else 'ua'
            )
        )

        # Update the session with the selected country
        await sync_to_async(request.session.__setitem__)(
            'selected_country', country
        )

        displayed_country_name = (
            COUNTRIES_UA.get(country, 'Unknown') if language == 'uk'
            else COUNTRIES.get(country, 'Unknown')
        )
        genitive_country_name = (
            COUNTRIES_GENITIVE_UA.get(country, 'Unknown') if language == 'uk'
            else COUNTRIES.get(country, 'Unknown')
        )

        # Clear session news data for a country
        news_session_key = f'news_data_{country}'
        await sync_to_async(request.session.pop)(news_session_key, None)

        # Download news
        news_data = await sync_to_async(cache.get)(news_session_key)
        if not news_data:
            news_data = {}
            try:
                for cat in CATEGORY_MAP.keys():
                    articles = await fetch_news_by_category(
                        cat, country, transl
                    )
                    news_data[cat] = articles
                await sync_to_async(request.session.__setitem__)(
                    news_session_key, news_data
                )
            except APIError:
                news_data = {cat: [] for cat in CATEGORY_MAP.keys()}
                context['error_message'] = transl['unable_to_fetch_news']

        articles = news_data.get(category, [])

        category_titles = {
            'general': transl['general_title'],
            'business': transl['business_title'],
            'entertainment': transl['entertainment_title'],
            'health': transl['health_title'],
            'science': transl['science_title'],
            'sports': transl['sports_title'],
            'technology': transl['technology_title']
        }
        category_title = category_titles.get(category, transl['default_title'])

        context.update({
            'selected_country': country,
            'selected_country_name': displayed_country_name,
            'genitive_country_name': genitive_country_name,
            'countries': COUNTRIES if language == 'en' else COUNTRIES_UA,
            'categories': list(CATEGORY_MAP.keys()),
            'selected_category': category,
            'category_translations': {
                k: transl[k] for k in CATEGORY_MAP.keys()
            },
            'articles': articles,
            'category_title': category_title
        })

        return render(request, 'newsapp/category_news.html', context)
