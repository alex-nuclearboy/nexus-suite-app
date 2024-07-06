from django.utils.translation import gettext as _


def get_translated_day_and_month(date):
    days_of_week = {
        'Monday': _('Monday'),
        'Tuesday': _('Tuesday'),
        'Wednesday': _('Wednesday'),
        'Thursday': _('Thursday'),
        'Friday': _('Friday'),
        'Saturday': _('Saturday'),
        'Sunday': _('Sunday'),
    }

    months = {
        'January': _('January'),
        'February': _('February'),
        'March': _('March'),
        'April': _('April'),
        'May': _('May'),
        'June': _('June'),
        'July': _('July'),
        'August': _('August'),
        'September': _('September'),
        'October': _('October'),
        'November': _('November'),
        'December': _('December'),
    }

    day_name = date.strftime('%A')
    month_name = date.strftime('%B')

    translated_day = days_of_week[day_name]
    translated_month = months[month_name]

    return translated_day, translated_month
