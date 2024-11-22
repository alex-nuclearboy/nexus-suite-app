import re

from django.forms import ValidationError
from django.contrib.auth.password_validation import (
    validate_password,
    get_default_password_validators
)

from .translations import translations


def validate_passwords(
        password1: str, password2: str, language: str = 'en'
) -> None:
    """
    Validate passwords for equality and complexity requirements.

    This function ensures that two provided passwords match and meet
    the complexity requirements as defined by Django's password validators.

    :param password1: The primary password input.
    :param password2: The confirmation password input.
    :param language: Language code for error message translations,
                     defaults to 'en'.

    :raises ValidationError: If the passwords do not match or fail
                             to meet complexity requirements.
    """
    # Fetch translations based on the specified language
    transl = translations.get(language, translations['en'])

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

        # If there are any error messages, raise a validation error
        if error_messages:
            raise ValidationError(error_messages)


def validate_username_format(username: str, error_message: str) -> None:
    """
    Validate the format of a username.

    A valid username must:
    - Start with a letter.
    - Contain only letters, numbers, or underscores.

    :param username: The username to validate.
    :param error_message: Custom error message to raise on validation failure.

    :raises ValidationError: If the username is invalid.
    """
    username_regex = r'^[a-zA-Z][a-zA-Z0-9_]*$'
    if not re.match(username_regex, username):
        raise ValidationError(error_message)


def validate_email_format(email: str, error_message: str) -> None:
    """
    Validate the format of an email address.

    A valid email must:
    - Have a standard email format (e.g., user@example.com).
    - Use only alphanumeric characters, dots, underscores, or hyphens
      before the "@" symbol.

    :param email: The email address to validate.
    :param error_message: Custom error message to raise on validation failure.

    :raises ValidationError: If the email is invalid.
    """
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        raise ValidationError(error_message)


def validate_name_field(value: str, error_message: str) -> str:
    """
    Validate a name field to ensure it contains only alphabetic
    characters and spaces.

    This function ensures that a name field is either empty or consists
    only of letters (a-z, A-Z, а-я, А-Я) and optional spaces.

    :param value: The input value to validate
    :param error_message: Custom error message to raise on validation failure.

    :return: The stripped input value if valid.
    :raises ValidationError: If the value does not meet format requirements.
    """
    if not value:
        return value  # Allow empty values if deletion is permitted

    if not value.isalpha() and not all(
        char.isalpha() or char.isspace() for char in value
    ):
        raise ValidationError(error_message)

    return value.strip()


def validate_phone_number(phone_number: str, translations: dict) -> str:
    """
    Validate and format a phone number.

    A valid phone number must:
    - Contain only digits, optionally start with '+' for international numbers.
    - Have at least 4 digits for local numbers.
    - For international numbers, have at least 10 digits after the '+' sign.

    :param phone_number: The phone number to validate.
    :param translations: A dictionary with translation keys for error messages.

    :return: The formatted and validated phone number.
    :raises ValidationError: If the phone number is invalid.
    """
    # Remove spaces, dashes, and parentheses
    formatted_phone = re.sub(r'[\s\-\(\)]', '', phone_number)

    # Validate phone number format
    if not re.match(r'^\+?\d+$', formatted_phone):
        raise ValidationError(translations['invalid_phone_number'])

    # Validate international numbers
    if formatted_phone.startswith('+'):
        if len(formatted_phone) < 11:
            raise ValidationError(
                translations['invalid_international_phone_number']
            )
        if not formatted_phone[1:].isdigit():
            raise ValidationError(
                translations['phone_number_after_plus_digits']
            )

    # Validate local numbers
    elif len(formatted_phone) < 4:
        raise ValidationError(translations['invalid_phone_number_min_length'])

    return formatted_phone
