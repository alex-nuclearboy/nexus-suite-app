DAYS_TRANSLATIONS = {
    'en': [
        'Monday', 'Tuesday', 'Wednesday', 'Thursday',
        'Friday', 'Saturday', 'Sunday'
    ],
    'uk': [
        'понеділок', 'вівторок', 'середа', 'четвер',
        'п\'ятниця', 'субота', 'неділя'
    ]
}

MONTHS_TRANSLATIONS = {
    'en': [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ],
    'uk': [
        'січня', 'лютого', 'березня', 'квітня', 'травня', 'червня',
        'липня', 'серпня', 'вересня', 'жовтня', 'листопада', 'грудня'
    ]
}


def get_translated_day_and_month(dt, language='en'):
    """
    Translate the day of the week and month name to the specified language.

    Parameters:
    dt (datetime): The datetime object to translate.
    language (str): The language code ('en' or 'uk').

    Returns:
    tuple: Translated day of the week and month name.
    """
    day_name = DAYS_TRANSLATIONS[language][dt.weekday()]
    month_name = MONTHS_TRANSLATIONS[language][dt.month - 1]
    return day_name, month_name
