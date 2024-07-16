import logging

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base class for all API related errors."""
    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response


class InvalidRequestError(APIError):
    """Raised when the request is invalid"""
    pass


class AuthenticationError(APIError):
    """Raised when there is an authentication error"""
    pass


class RateLimitError(APIError):
    """Raised when the rate limit is exceeded"""
    pass


class ServerError(APIError):
    """Raised when there is an internal server error"""
    pass


class UnexpectedError(APIError):
    """Raised when an unexpected error occurs"""
    pass


class InternalServerError(APIError):
    """
    Raised when there is an internal server error with the API.
    This indicates that there is an issue on the API provider's side.
    """
    pass


class TimeoutError(APIError):
    """
    Raised when the API request times out.
    This indicates that the request took too long to complete.
    """
    pass


class InvalidResponseError(APIError):
    """
    Raised when the API response contains invalid data or cannot be parsed.
    This indicates that the response could not be processed as expected.
    """
    pass


class ContentTypeError(APIError):
    """
    Raised when the API response contains an unexpected content type.
    This indicates that the response could not be parsed as JSON.
    """
    pass


class CurrencyConversionError(Exception):
    """Base class for all currency conversion related errors"""
    pass


class ZeroDivisionCurrencyError(CurrencyConversionError):
    """Raised when a division by zero occurs in currency conversion"""
    pass


class InvalidCurrencyRateError(CurrencyConversionError):
    """Raised when a currency rate is invalid (e.g., not a number)"""
    pass


class GeocodingError(APIError):
    """Base class for all geocoding related errors"""
    pass


class GeocodingInvalidRequestError(GeocodingError):
    """Raised when the geocoding request is invalid"""
    pass


class GeocodingAuthenticationError(GeocodingError):
    """
    Raised when there is an authentication error
    with the geocoding service
    """
    pass


class GeocodingQuotaExceededError(GeocodingError):
    """Raised when the geocoding request quota has been exceeded"""
    pass


class GeocodingForbiddenError(GeocodingError):
    """Raised when the geocoding request is forbidden"""
    pass


class GeocodingInvalidEndpointError(GeocodingError):
    """Raised when the geocoding endpoint is invalid"""
    pass


class GeocodingMethodNotAllowedError(GeocodingError):
    """
    Raised when the HTTP method used in the geocoding request is not allowed
    """
    pass


class GeocodingTimeoutError(GeocodingError):
    """Raised when the geocoding request times out"""
    pass


class GeocodingRequestTooLongError(GeocodingError):
    """Raised when the geocoding request is too long"""
    pass


class GeocodingUpgradeRequiredError(GeocodingError):
    """Raised when the geocoding request requires an upgrade"""
    pass


class GeocodingRateLimitError(GeocodingError):
    """Raised when the rate limit for geocoding requests has been exceeded"""
    pass


class GeocodingInternalServerError(GeocodingError):
    """
    Raised when there is an internal server error with the geocoding service
    """
    pass


class InvalidAPIKeyError(APIError):
    """Raised when the provided API key is invalid."""
    pass


class CityNotFoundError(GeocodingError):
    """Raised when the specified city is not found by the API."""
    pass


class UnableToRetrieveWeatherError(APIError):
    """Raised when the weather data cannot be retrieved from the API."""
    pass


class RateLimitExceededError(APIError):
    """Raised when the API key has exceeded the allowed call quota."""
    pass


# class InvalidRequestError(APIError):
#     """Raised for various invalid request errors."""
#     pass


class InternalApplicationError(APIError):
    """Raised when there is an internal application error."""
    pass


class InvalidJSONResponseError(APIError):
    """Raised when the API response contains invalid JSON."""
    pass


class IncompleteWeatherDataError(APIError):
    """Raised when the weather data from the API is incomplete."""
    pass


async def handle_news_api_error(response):
    """
    Handle errors based on the response status code and error code
    in the JSON response.

    Parameters:
    - response: The HTTP response object

    Raises:
    - Appropriate exception based on the response status code and error code
    """
    try:
        data = await response.json()
    except ValueError:
        logger.error("Invalid JSON response")
        raise UnexpectedError("Invalid JSON response")

    error_code = data.get('code', 'unexpectedError')
    error_msg = data.get('message', 'Unknown error')

    if response.status == 400:
        if error_code in ['parameterInvalid', 'parametersMissing']:
            logger.error(f"Invalid request: {error_msg}")
            raise InvalidRequestError(error_msg)
    elif response.status == 401:
        if error_code in [
            'apiKeyDisabled', 'apiKeyExhausted',
            'apiKeyInvalid', 'apiKeyMissing'
        ]:
            logger.error(f"Authentication error: {error_msg}")
            raise AuthenticationError(error_msg)
    elif response.status == 429:
        if error_code == 'rateLimited':
            logger.error(f"Rate limit exceeded: {error_msg}")
            raise RateLimitError(error_msg)
    elif response.status == 500:
        logger.error(f"Server error: {error_msg}")
        raise ServerError(error_msg)
    else:
        logger.error(f"Unexpected error: {error_msg}")
        raise UnexpectedError(error_msg)


async def handle_exchange_api_error(response):
    """
    Handle errors based on the response status code and error code
    in the JSON response.

    Parameters:
    - response: The HTTP response object

    Raises:
    - Appropriate exception based on the response status code and error code
    """
    try:
        data = await response.json()
    except ValueError:
        logger.error("Invalid JSON response or unexpected content type")
        raise ContentTypeError(
            "Invalid JSON response or unexpected content type"
        )

    error_msg = data.get('message', 'Unknown error')

    if response.status == 400:
        logger.error(f"Invalid request: {error_msg}")
        raise InvalidRequestError(error_msg)
    elif response.status == 500:
        logger.error(f"Internal server error: {error_msg}")
        raise InternalServerError(error_msg)
    elif response.status == 503:
        logger.error(f"Service unavailable: {error_msg}")
        raise InternalServerError(error_msg)
    elif response.status == 408:
        logger.error(f"Request timeout: {error_msg}")
        raise TimeoutError(error_msg)
    else:
        logger.error(f"Unexpected error: {error_msg}")
        raise UnexpectedError(error_msg)


async def handle_geocoding_api_error(response):
    """
    Handle errors based on the response status code and error code
    in the JSON response.

    Parameters:
    - response: The HTTP response object

    Raises:
    - Appropriate exception based on the response status code and error code
    """
    try:
        data = await response.json()
    except ValueError:
        logger.error("Invalid JSON response")
        raise GeocodingError("Invalid JSON response")

    error_msg = data.get('status', {}).get('message', 'Unknown error')

    if response.status == 400:
        logger.error(f"Geocoding error: Invalid request - {error_msg}")
        raise GeocodingInvalidRequestError(f"{error_msg}")
    elif response.status == 401:
        logger.error(f"Geocoding error: Authentication error - {error_msg}")
        raise GeocodingAuthenticationError(f"{error_msg}")
    elif response.status == 402:
        logger.error(f"Geocoding error: Quota exceeded - {error_msg}")
        raise GeocodingQuotaExceededError(f"{error_msg}")
    elif response.status == 403:
        logger.error(f"Geocoding error: Forbidden - {error_msg}")
        raise GeocodingAuthenticationError(f"{error_msg}")
    elif response.status == 404:
        logger.error(f"Geocoding error: Invalid endpoint - {error_msg}")
        raise GeocodingInvalidRequestError(f"{error_msg}")
    elif response.status == 405:
        logger.error(f"Geocoding error: Method not allowed - {error_msg}")
        raise GeocodingInvalidRequestError(f"{error_msg}")
    elif response.status == 408:
        logger.error(f"Geocoding error: Timeout - {error_msg}")
        raise GeocodingTimeoutError(f"{error_msg}")
    elif response.status == 429:
        logger.error(f"Geocoding error: Rate limit exceeded - {error_msg}")
        raise GeocodingRateLimitError(f"{error_msg}")
    elif response.status == 500:
        logger.error(f"Geocoding error: Internal server error - {error_msg}")
        raise GeocodingInternalServerError(f"{error_msg}")
    else:
        logger.error(f"Geocoding error: {error_msg}")
        raise GeocodingError(f"{error_msg}")


async def handle_weather_api_error(response, transl):
    """
    Handle errors based on the response status code and error code
    in the JSON response.

    Parameters:
    - response: The HTTP response object
    - transl: Translations dictionary for error messages

    Raises:
    - Appropriate exception based on the response status code and error code
    """
    try:
        data = await response.json()
    except ValueError:
        logger.error("Invalid JSON response")
        raise InvalidRequestError("Invalid JSON response")

    error_code = data.get('error', {}).get('code', 'unknown')
    error_msg = data.get('error', {}).get('message', 'Unknown error')

    if response.status == 400:
        if error_code in ['1003', '1005', '9000', '9001', '9999']:
            logger.error(f"Invalid request: {error_msg}")
            raise InvalidRequestError(error_msg)
        if error_code == '1006':
            logger.error(f"City not found: {error_msg}")
            raise CityNotFoundError(error_msg)
    elif response.status == 401:
        if error_code == '1002':
            logger.error(f"API key not provided: {error_msg}")
            raise InvalidAPIKeyError(error_msg)
        if error_code == '2006':
            logger.error(f"Invalid API key: {error_msg}")
            raise InvalidAPIKeyError(error_msg)
    elif response.status == 403:
        if error_code in ['2007', '2008', '2009']:
            logger.error(f"Rate limit exceeded: {error_msg}")
            raise RateLimitExceededError(error_msg)
    elif response.status == 500:
        logger.error(f"Internal application error: {error_msg}")
        raise InternalApplicationError(error_msg)
    else:
        logger.error(f"Unable to retrieve weather: {error_msg}")
        raise UnableToRetrieveWeatherError(error_msg)


class TranslationError(Exception):
    """Base class for all translation related errors."""
    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response


class WikipediaAPIError(TranslationError):
    """Raised when there is an error with the Wikipedia API request."""
    pass


class JSONDecodingError(TranslationError):
    """Raised when there is an error decoding the JSON response."""
    pass


class NameNotFoundError(TranslationError):
    """Raised when the country or region name is not found in the response.
    """
    pass
