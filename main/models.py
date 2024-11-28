from mongoengine import (
    Document, StringField, ListField, ReferenceField, DateTimeField
)


class Author(Document):
    """
    Represent an author in the MongoDB database.

    Fields:
        fullname -- The full name of the author.
        born_date -- The birth date of the author.
        born_location -- The location where the author was born.
        description -- A short description of the author.
    """
    meta = {'collection': 'authors'}
    fullname = StringField(required=True)
    born_date = DateTimeField()
    born_location = StringField()
    description = StringField()


class Quote(Document):
    """
    Represent a quote in the MongoDB database.

    Fields:
        quote -- The text of the quote.
        author -- A reference to an Author document.
        tags -- A list of tags associated with the quote.
    """
    meta = {'collection': 'quotes'}
    quote = StringField(required=True)
    author = ReferenceField(Author, required=True)
    tags = ListField(StringField())
