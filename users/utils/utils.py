from django import forms
from django.contrib.auth.password_validation import (
    validate_password,
    get_default_password_validators
)

from .translations import translations


def validate_passwords(password1, password2, language='en'):
    """
    Custom password validator that checks if passwords match
    and follow the required format and complexity.

    :param password1: The first password input by the user.
    :type password1: str
    :param password2: The second password input (typically for confirmation).
    :type password2: str
    :param language: The language code for translations, defaults to 'en'.
    :type language: str, optional

    :raises forms.ValidationError: If the passwords do not match or fail
                                   to meet complexity requirements.
    """
    # Check for password matching
    if password1 and password2 and password1 != password2:
        raise forms.ValidationError(
            translations.get(language, translations['en'])['password_mismatch']
        )

    # Check the password format using Django's default validators
    try:
        validate_password(
                    password1,
                    password_validators=get_default_password_validators()
                )
    except forms.ValidationError as e:
        # If validation errors occur, collect and translate error messages
        error_messages = []
        for message in e.messages:
            # Check if the error message contains specific text
            # and map it to a translation
            if 'too short' in message:
                error_messages.append(
                    translations.get(language, translations['en'])
                    ['password_too_short']
                )
            elif 'too common' in message:
                error_messages.append(
                    translations.get(language, translations['en'])
                    ['password_too_common']
                )
            elif 'entirely numeric' in message:
                error_messages.append(
                    translations.get(language, translations['en'])
                    ['password_entirely_numeric']
                )
            else:
                # For other error messages, use the original message
                error_messages.append(message)

        # If there are any error messages, raise a validation error
        if error_messages:
            raise forms.ValidationError(error_messages)
