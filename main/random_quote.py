import random
from mongoengine import Document, StringField


# Ваша модель цитати
class Quote(Document):
    text = StringField(required=True)
    author = StringField(required=True)


# Функція для отримання випадкової цитати
def get_random_quote():
    """
    Get a random quote from the MongoDB database.
    """
    # Отримуємо всі цитати з бази даних
    all_quotes = Quote.objects.all()

    # Якщо в базі є цитати, вибираємо одну випадкову
    if all_quotes:
        random_quote = random.choice(all_quotes)
        return random_quote
    return None
