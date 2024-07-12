from django import template
from datetime import datetime
from ..utils.utils import format_time

register = template.Library()


@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.filter
def format_time_filter(date_string, lang='en', format_type='abbr'):
    return format_time(date_string, lang, format_type)


@register.filter
def format_time_24h(date_string):
    """
    Converts time from 12-hour AM/PM format to 24-hour format.
    """
    # Parse the date_string into a datetime object
    try:
        # Assuming the time is in "%I:%M %p" format, e.g., "05:01 PM"
        dt = datetime.strptime(date_string, "%I:%M %p")
        # Return time in 24-hour format
        return dt.strftime("%H:%M")
    except ValueError:
        return date_string  # Return original if there is an error
