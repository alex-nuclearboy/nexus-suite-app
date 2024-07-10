from django import template
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
