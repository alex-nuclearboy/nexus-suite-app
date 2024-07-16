from django.core.cache import cache

from datetime import datetime
from asgiref.sync import sync_to_async
from aiohttp import ClientSession

from .exceptions import handle_exchange_api_error

# Currency name mappings for different languages
CURRENCY_MAP = {
    'en': {
        'USD': 'US Dollar',
        'EUR': 'Euro',
        'GBP': 'British Pound',
        'PLN': 'Polish Zloty',
        'CHF': 'Swiss Franc',
        'CZK': 'Czech Koruna',
        'UAH': 'Ukrainian Hryvnia'
    },
    'uk': {
        'USD': 'долар США',
        'EUR': 'євро',
        'GBP': 'британський фунт',
        'PLN': 'польський злотий',
        'CHF': 'швейцарський франк',
        'CZK': 'чеська крона',
        'UAH': 'українська гривня'
    }
}

API_URL = 'https://api.privatbank.ua/p24api/exchange_rates?json&date='


async def fetch_exchange_rates(filter_currencies=None):
    """
    Fetches and caches exchange rates data from PrivatBank API.

    This function retrieves the exchange rates for the required currencies
    from the PrivatBank API. The data is cached for 10 minutes to improve
    performance.

    Parameters:
    filter_currencies (set, optional): A set of currency codes to filter the
                                       exchange rates. Defaults to None.

    Returns:
    list: A list of exchange rates for the required currencies.
    """
    cache_key = 'exchange_rates'
    exchange_rates = await sync_to_async(cache.get)(cache_key)

    if not exchange_rates:
        today = datetime.today().strftime('%d.%m.%Y')
        url = f'{API_URL}{today}'

        async with ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    await handle_exchange_api_error(response)

                data = await response.json()

                exchange_rates = [
                    rate for rate in data['exchangeRate']
                    if 'currency' in rate and rate['currency'] != 'UAH'
                ]

                # Sort exchange rates by custom order
                custom_order = {
                    'USD': 1, 'EUR': 2, 'GBP': 3, 'CHF': 4, 'PLN': 5, 'CZK': 6
                }
                exchange_rates.sort(
                    key=lambda x: custom_order.get(x['currency'], 999)
                )

                # Cache the exchange rates for 10 minutes (600 seconds)
                await sync_to_async(cache.set)(cache_key, exchange_rates, 600)

    # Apply filtering if filter_currencies is provided
    if filter_currencies:
        exchange_rates = [
            rate for rate in exchange_rates
            if rate['currency'] in filter_currencies
        ]

    return exchange_rates


async def convert_currency(
        amount, from_currency, to_currency, exchange_rates, transl
):
    """
    Converts an amount from one currency to another using exchange rates.

    This function converts the given amount from the source currency to the
    target currency using the provided exchange rates. It handles UAH as the
    base currency.

    Parameters:
    amount (float): The amount of money to be converted.
    from_currency (str): The currency code of the source currency.
    to_currency (str): The currency code of the target currency.
    exchange_rates (list): A list of exchange rates.

    Returns:
    float: The converted amount in the target currency, rounded to 2 decimal
           places. Returns None if conversion rates are not found.
    """
    from_currency_buy_rate = None
    to_currency_sale_rate = None

    # Handling UAH as the base currency
    if from_currency == 'UAH':
        from_currency_buy_rate = 1
    if to_currency == 'UAH':
        to_currency_sale_rate = 1

    for rate in exchange_rates:
        if rate['currency'] == from_currency:
            from_currency_buy_rate = rate.get(
                'purchaseRate', rate.get('saleRate')
            )
        if rate['currency'] == to_currency:
            to_currency_sale_rate = rate.get(
                'saleRate', rate.get('purchaseRate')
            )

    if from_currency_buy_rate is None or to_currency_sale_rate is None:
        error_message = transl['conversion_rate_not_found']
        return None, error_message

    try:
        amount_in_uah = amount * from_currency_buy_rate
        converted_amount = amount_in_uah / to_currency_sale_rate
        return round(converted_amount, 2), None
    except ZeroDivisionError:
        error_message = transl['conversion_division_error']
        return None, error_message
    except Exception as e:
        error_message = str(e)
        return None, error_message
