class APIError(Exception):
    """Base class for all API related errors"""
    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response


class InvalidRequestError(APIError):
    """
    Raised when the API request is invalid.
    This could be due to a missing parameter, invalid coordinates,
    or an invalid format.
    """
    pass


class AuthenticationError(APIError):
    """
    Raised when there is an authentication error with the API.
    This could be due to a missing, invalid, or unknown API key.
    """
    pass


class QuotaExceededError(APIError):
    """
    Raised when the API request quota has been exceeded.
    This indicates that the user has surpassed their allocated API usage limit.
    """
    pass


class ForbiddenError(APIError):
    """
    Raised when the API request is forbidden.
    This could be due to the API key being disabled or the IP address
    being rejected.
    """
    pass


class InvalidEndpointError(APIError):
    """
    Raised when the API endpoint is invalid.
    This indicates that the requested endpoint does not exist.
    """
    pass


class MethodNotAllowedError(APIError):
    """
    Raised when the HTTP method used in the API request is not allowed.
    This typically means a non-GET request was made to an endpoint that only
    accepts GET requests.
    """
    pass


class TimeoutError(APIError):
    """
    Raised when the API request times out.
    This indicates that the request took too long to complete.
    """
    pass


class RequestTooLongError(APIError):
    """
    Raised when the API request is too long.
    This typically means that the request exceeds the allowed length.
    """
    pass


class UpgradeRequiredError(APIError):
    """
    Raised when the API request requires an upgrade.
    This indicates that the current protocol version is not supported
    and an upgrade is needed.
    """
    pass


class RateLimitError(APIError):
    """
    Raised when the rate limit for API requests has been exceeded.
    This indicates that too many requests have been made in a short
    period of time.
    """
    pass


class InternalServerError(APIError):
    """
    Raised when there is an internal server error with the API.
    This indicates that there is an issue on the API provider's side.
    """
    pass


class InvalidAPIKeyError(AuthenticationError):
    """
    Raised when the provided API key is invalid.
    This is a specific type of AuthenticationError.
    """
    pass


class CityNotFoundError(APIError):
    """
    Raised when the specified city is not found by the API.
    This indicates that the city name provided does not match
    any known locations.
    """
    pass


class UnableToRetrieveWeatherError(APIError):
    """
    Raised when the weather data cannot be retrieved from the API.
    This could be due to various reasons, including server issues
    or invalid request parameters.
    """
    pass


class InvalidJSONResponseError(APIError):
    """
    Raised when the API response contains invalid JSON.
    This indicates that the response could not be parsed as JSON.
    """
    pass


class IncompleteWeatherDataError(APIError):
    """
    Raised when the API response contains incomplete weather data.
    This indicates that the response did not include all expected weather
    data fields.
    """
    pass


class GeocodingServiceError(APIError):
    """
    Raised when there is an error with the geocoding service.
    This indicates that there was an issue contacting the geocoding service
    or processing its response.
    """
    pass


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
    """Raised when the country or region name is not found in the response."""
    pass


def handle_api_error(response, transl):
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
        data = response.json()
    except ValueError:
        raise InvalidJSONResponseError(transl['invalid_JSON_response'])

    if response.status_code == 200:
        return

    error_code = data.get('error', {}).get('code', None)
    error_msg = data.get('error', {}).get('message', transl['unknown_error'])

    if response.status_code == 400:
        if error_code == 1003:
            raise InvalidRequestError(transl['invalid_request'])
        if error_code == 1005:
            raise InvalidEndpointError(transl['invalid_endpoint'])
        if error_code == 1006:
            raise CityNotFoundError(
                transl['city_not_found'] % {'city': transl['unknown']}
            )
        if error_code == 9000:
            raise InvalidRequestError(transl['invalid_json'])
        if error_code == 9001:
            raise RequestTooLongError(transl['too_many_locations'])
        raise InvalidRequestError(error_msg)
    if response.status_code == 401:
        if error_code == 1002:
            raise InvalidAPIKeyError(transl['api_key_missing'])
        if error_code == 2006:
            raise InvalidAPIKeyError(transl['invalid_key'])
        raise AuthenticationError(error_msg)
    if response.status_code == 402:
        raise QuotaExceededError(transl['quota_exceeded'])
    if response.status_code == 403:
        if error_code == 2008:
            raise ForbiddenError(transl['api_key_disabled'])
        if error_code == 2009:
            raise ForbiddenError(transl['access_denied'])
        raise ForbiddenError(error_msg)
    if response.status_code == 404:
        raise InvalidEndpointError(transl['invalid_endpoint'])
    if response.status_code == 405:
        raise MethodNotAllowedError(transl['method_not_allowed'])
    if response.status_code == 408:
        raise TimeoutError(transl['timeout'])
    if response.status_code == 410:
        raise RequestTooLongError(transl['request_too_long'])
    if response.status_code == 426:
        raise UpgradeRequiredError(transl['upgrade_required'])
    if response.status_code == 429:
        raise RateLimitError(transl['rate_limit_exceeded'])
    if response.status_code == 503:
        raise InternalServerError(transl['internal_server_error'])

    raise UnableToRetrieveWeatherError(error_msg)
