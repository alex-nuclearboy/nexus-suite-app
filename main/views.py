from django.shortcuts import render

from .random_quote import get_random_quote


def random_quote_view(request):
    # Отримуємо випадкову цитату
    random_quote = get_random_quote()

    # Передаємо цитату в шаблон
    return render(request, 'random_quote.html', {'random_quote': random_quote})
