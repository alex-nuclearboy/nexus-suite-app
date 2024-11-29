from datetime import datetime
from mongoengine import (
    Document, StringField, ListField,
    ReferenceField, DateTimeField, BooleanField
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
    meta = {
        'collection': 'authors',
        'indexes': ['fullname']
    }
    fullname = StringField(required=True, unique=True)
    born_date = DateTimeField(validation=lambda d: d <= datetime.utcnow())
    born_location = StringField()
    description = StringField()
    is_active = BooleanField(default=True)


class Tag(Document):
    """
    Represent a tag in the MongoDB database.

    Fields:
        name -- The name of the tag (unique).
        is_active -- Flag for soft deletion.
    """
    meta = {
        'collection': 'tags',
        'indexes': ['name']
    }
    name = StringField(required=True, unique=True)
    is_active = BooleanField(default=True)


class Quote(Document):
    """
    Represent a quote in the MongoDB database.

    Fields:
        quote -- The text of the quote.
        author -- A reference to an Author document.
        tags -- A list of tags associated with the quote.
    """
    meta = {
        'collection': 'quotes',
        'indexes': ['quote', 'tags']
    }
    quote = StringField(required=True)
    author = ReferenceField(Author, required=True)
    tags = ListField(ReferenceField(Tag))
    is_active = BooleanField(default=True)
