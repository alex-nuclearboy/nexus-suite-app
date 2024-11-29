from django.shortcuts import render
from .utils.utils import get_random_quote


def random_quote_view(request):
    """
    View to display a random quote along with the author's full name.

    This view retrieves a random quote from the database using
    the `get_random_quote` utility function. It ensures the quote is returned
    along with the author's full name. If no author is found for the quote,
    it defaults to "Unknown Author".

    :param request: The HTTP request object.
    :type request: HttpRequest

    :return: A rendered response with the random quote and author information.
    :rtype: HttpResponse
    """
    # Define the template path for rendering
    template_name = 'main/random_quote.html'

    # Get a random quote object using the utility function
    quote = get_random_quote()

    # Check if quote exists, otherwise show a fallback message
    if quote:
        if quote.author:
            author_name = quote.author.fullname
        else:
            author_name = "Unknown Author"
    else:
        quote = None
        author_name = None

    error_message = "Quote currently unavailable. Please try again later."

    # Render the template with the quote and author data
    return render(request, template_name, {
        'random_quote': quote,
        'author': author_name,
        'error_message': error_message if not quote else None
    })
