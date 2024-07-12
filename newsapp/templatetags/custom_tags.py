from django import template
from django.templatetags.static import static
from django.utils.safestring import mark_safe

register = template.Library()

# Dedicated moon phases dictionary
moon_phases = {
    'New Moon': {
        'icon': 'new_moon.png',
        'translations': {'en': 'New Moon', 'uk': 'Новий місяць'}
    },
    'Waxing Crescent': {
        'icon': 'waxing_crescent.png',
        'translations': {'en': 'Waxing Crescent', 'uk': 'Молодий Місяць'}
    },
    'First Quarter': {
        'icon': 'first_quarter.png',
        'translations': {'en': 'First Quarter', 'uk': 'Перша чверть'}
    },
    'Waxing Gibbous': {
        'icon': 'waxing_gibbous.png',
        'translations': {'en': 'Waxing Gibbous', 'uk': 'Прибуваючий Місяць'}
    },
    'Full Moon': {
        'icon': 'full_moon.png',
        'translations': {'en': 'Full Moon', 'uk': 'Повний місяць'}
    },
    'Waning Gibbous': {
        'icon': 'waning_gibbous.png',
        'translations': {'en': 'Waning Gibbous', 'uk': 'Спадаючий Місяць'}
    },
    'Last Quarter': {
        'icon': 'last_quarter.png',
        'translations': {'en': 'Last Quarter', 'uk': 'Остання чверть'}
    },
    'Waning Crescent': {
        'icon': 'waning_crescent.png',
        'translations': {'en': 'Waning Crescent', 'uk': 'Старий Місяць'}
    }
}


@register.simple_tag
def moon_phase_icon(phase, language):
    phase_info = moon_phases.get(
        phase, {'icon': 'default.png', 'translations': {language: phase}}
    )
    icon_url = static(f"newsapp/icons/{phase_info['icon']}")
    translated_phase = phase_info['translations'].get(language, phase)

    html_output = mark_safe(
        f"<div style='display: flex; align-items: center; "
        f"justify-content: left;'><img src='{icon_url}' "
        f"alt='{translated_phase}' title='{translated_phase}' "
        f"style='width: 30px; height: auto;'>"
        f"<span style='margin-left: 10px; font-weight: 600; font-size: 16px;'>"
        f"{translated_phase}</span></div>"
    )

    return html_output
