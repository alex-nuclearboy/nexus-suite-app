import logging
from mongoengine.errors import DoesNotExist, OperationError
from pymongo.errors import (
    OperationFailure, ConfigurationError, ServerSelectionTimeoutError
)

from ..models import Quote

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_random_quote():
    """
    Retrieve a random quote from the database along with its author.

    This function uses MongoDB's aggregation framework to randomly select
    a quote from the collection. It then ensures the quote's author is loaded.
    Additionally, any curly quotes (like “ and ”) are removed.

    :return: Quote object containing the quote text and author information,
             or None if no quote is found.
    :rtype: Quote or None
    """
    try:
        # Use aggregation with $sample to get a random quote
        random_quote_cursor = Quote.objects.aggregate(
            [{'$sample': {'size': 1}}]
        )

        # Convert the cursor to a list and get the first item
        random_quote_list = list(random_quote_cursor)

        if not random_quote_list:
            logger.info(" No quotes found.")
            return None

        # Access the first item from the list
        random_quote = random_quote_list[0]

        # Retrieve the full Quote document by its ID
        # including the Author reference
        quote = Quote.objects(id=random_quote['_id']) \
            .only('quote', 'author') \
            .first()

        if quote:
            try:
                # Attempt to reload the author
                quote.author.reload()
            except DoesNotExist:
                # If the author does not exist
                quote.author = None
                logger.warning(" Author document does not exist.")

            if quote.quote:
                # Remove curly quotes (e.g., “ and ”)
                quote.quote = quote.quote.replace('“', '').replace('”', '')

        return quote

    except (
        OperationFailure, ConfigurationError, ServerSelectionTimeoutError
    ) as e:
        logger.error(f" MongoDB connection failed: {e}")
    except OperationError as e:
        logger.error(f" MongoDB operation error: {e}")
    except Exception as e:
        logger.error(f" An unexpected error occurred: {e}")

    return None
