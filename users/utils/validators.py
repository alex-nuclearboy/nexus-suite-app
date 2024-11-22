import re
from datetime import datetime

from django.forms import ValidationError
from django.contrib.auth.password_validation import (
    validate_password,
    get_default_password_validators
)

from .translations import translations


USERNAME_REGEX = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]*$')
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
PHONE_NUMBER_REGEX = re.compile(r'^\+?\d+$')


def get_translations(language: str) -> dict:
    return translations.get(language, translations['en'])


def validate_passwords(
        password1: str, password2: str, language: str = 'en'
) -> None:
    """
    Validate that the provided passwords are equal
    and meet the complexity requirements.

    This function ensures that the two provided passwords match and meet the
    complexity requirements as defined by Django's password validators.

    :param password1: The first password input.
    :param password2: The second (confirmation) password input.
    :param language: Language code for error message translations,
                     defaults to 'en'.

    :raises ValidationError: If the passwords do not match or fail
                             to meet complexity requirements.
    """
    transl = get_translations(language)

    # Ensure passwords match
    if password1 and password2 and password1 != password2:
        raise ValidationError(transl['password_mismatch'])

    # Validate password complexity using Django's validators
    try:
        validate_password(
                    password1,
                    password_validators=get_default_password_validators()
                )
    except ValidationError as e:
        # Translate error messages, if applicable
        error_messages = []
        for message in e.messages:
            # Check if the error message contains specific text
            # and map it to a translation
            if 'too short' in message:
                error_messages.append(transl['password_too_short'])
            elif 'too common' in message:
                error_messages.append(transl['password_too_common'])
            elif 'entirely numeric' in message:
                error_messages.append(transl['password_entirely_numeric'])
            else:
                # For other error messages, use the original message
                error_messages.append(message)

        # Raise ValidationError with translated error messages
        if error_messages:
            raise ValidationError(error_messages)


def validate_username_format(username: str, language: str = 'en') -> None:
    """
    Validate the format of a username.

    A valid username must:
    - Start with a letter.
    - Contain only letters, numbers, or underscores.

    :param username: The username to validate.
    :param language: Language code for error message translations,
                     defaults to 'en'.

    :raises ValidationError: If the username is invalid.
    """
    transl = get_translations(language)

    if not USERNAME_REGEX.match(username):
        raise ValidationError(transl['invalid_username_format'])


def validate_email_format(email: str, language: str = 'en') -> None:
    """
    Validate the format of an email address.

    A valid email must:
    - Have a standard email format (e.g., user@example.com).
    - Contain only alphanumeric characters, dots, underscores,
      or hyphens before the "@" symbol.

    :param email: The email address to validate.
    :param language: Language code for error message translations,
                     defaults to 'en'.

    :raises ValidationError: If the email is invalid.
    """
    transl = get_translations(language)

    if not EMAIL_REGEX.match(email):
        raise ValidationError(transl['invalid_email_format'])


def validate_name_field(value: str, language: str = 'en') -> str:
    """
    Validate that a name contains only alphabetic characters and spaces,
    and format each word with the first letter capitalized and the rest
    in lowercase.

    This function ensures that a name is either empty or consists
    only of letters (a-z, A-Z, а-я, А-Я) and optional spaces,
    and then formats each word with the first letter capitalized.

    :param value: The input value to validate and format.
    :param language: Language code for error message translations,
                     defaults to 'en'.

    :return: The formatted and validated name.

    :raises ValidationError: If the value does not meet format requirements.
    """
    transl = get_translations(language)

    if not value:
        return value  # Allow empty values

    if not value.isalpha() and not all(
        char.isalpha() or char.isspace() for char in value
    ):
        raise ValidationError(transl['invalid_name_format'])

    # Format each word with the first letter capitalized
    # and the rest in lowercase
    formatted_value = ' '.join([word.capitalize() for word in value.split()])

    return formatted_value.strip()


def validate_phone_number(phone_number: str, language: str = 'en') -> str:
    """
    Validate and format a phone number.

    A valid phone number must:
    - Contain only digits, optionally start with '+' for international numbers.
    - Have at least 4 digits for local numbers.
    - For international numbers, have at least 10 digits after the '+' sign.

    :param phone_number: The phone number to validate.
    :param language: Language code for error message translations,
                     defaults to 'en'.

    :return: The formatted and validated phone number.

    :raises ValidationError: If the phone number is invalid.
    """
    transl = get_translations(language)

    # Remove spaces, dashes, and parentheses
    formatted_phone = re.sub(r'[\s\-\(\)]', '', phone_number)

    # Validate phone number format
    if not PHONE_NUMBER_REGEX.match(formatted_phone):
        raise ValidationError(transl['invalid_phone_number'])

    # Validate international numbers
    if formatted_phone.startswith('+'):
        if len(formatted_phone) < 11:
            raise ValidationError(transl['invalid_international_phone_number'])
        if not formatted_phone[1:].isdigit():
            raise ValidationError(transl['phone_number_after_plus_digits'])

    # Validate local numbers
    elif len(formatted_phone) < 4:
        raise ValidationError(transl['invalid_phone_number_min_length'])

    return formatted_phone


def validate_date_of_birth(
        date_of_birth: str, language: str = 'en'
) -> datetime.date:
    """
    Validate the date of birth to ensure it's in a valid format,
    not in the future, and not too old.

    :param date_of_birth: The date of birth to validate.
    :param language: Language code for error message translations,
                     defaults to 'en'.

    :return: The validated date of birth.

    :raises ValidationError: If the date of birth is invalid.
    """
    transl = get_translations(language)

    if not date_of_birth:
        return None  # Allow deletion by returning None

    # Check the date format
    try:
        if isinstance(date_of_birth, str):
            date_of_birth = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError(transl['invalid_date'])

    # Check for future dates
    if date_of_birth > datetime.today().date():
        raise ValidationError(transl['dob_in_future'])

    # Check if the date is too old
    if date_of_birth < datetime(1900, 1, 1).date():
        raise ValidationError(transl['dob_too_old'])

    return date_of_birth
