from django import template
import datetime

register = template.Library()

MONTHS_TRANSLATIONS = {
    'en': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
    'uk': ['січ', 'лют', 'бер', 'кві', 'тра', 'чер',
           'лип', 'сер', 'вер', 'жов', 'лис', 'гру']
}


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def translate_month(value, lang='en'):
    if isinstance(value, datetime.date):
        month_index = value.month - 1
        return MONTHS_TRANSLATIONS[lang][month_index]
    return value
