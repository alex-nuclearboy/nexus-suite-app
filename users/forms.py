import re
import io
from PIL import Image

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.forms import (
    UserCreationForm, AuthenticationForm,
    PasswordResetForm, SetPasswordForm
)

from .models import Profile
from .utils.translations import translations
from .utils.validators import (
    validate_passwords, validate_username_format, validate_email_format,
    validate_name_field, validate_phone_number, validate_date_of_birth
)


class BaseUserForm:
    """
    Mixin for forms to handle field translation and dynamic attribute updates.

    :param language: Language code for translations (default: 'en').
    :type language: str
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the form, set the translation dictionary,
        and update field attributes.

        :param args: Positional arguments passed to the form constructor.
        :type args: tuple
        :param kwargs: Keyword arguments passed to the form constructor.
        :type kwargs: dict
        """
        self.language = kwargs.pop('language', 'en')
        self.transl = translations.get(self.language, translations['en'])
        super().__init__(*args, **kwargs)
        self._update_field_attributes()
        self._update_error_messages()

    def clean_username(self):
        """
        Validate the uniqueness of the username.

        :return: Validated username.
        :rtype: str

        :raises forms.ValidationError: If the username is invalid
                                       or already exists.
        """
        if 'username' not in self.cleaned_data:
            return

        username = self.cleaned_data.get('username')

        if username:
            validate_username_format(username, self.language)
            if User.objects.filter(username=username).exists():
                raise forms.ValidationError(self.transl["username_exists"])

        return username

    def clean_email(self):
        """
        Validate the uniqueness of the email.

        :return: Validated email.
        :rtype: str

        :raises forms.ValidationError: If the email is invalid
                                       or already exists.
        """
        if 'email' not in self.cleaned_data:
            return

        email = self.cleaned_data.get('email')

        if email:
            validate_email_format(email, self.language)
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError(self.transl["email_exists"])

        return email

    def clean_first_name(self):
        """
        Validate the first name for valid characters
        (letters and spaces, and allows international characters).

        :return: Validated and formated first name.
        :rtype: str

        :raises forms.ValidationError: If the first name contains invalid
                                       characters.
        """
        if 'first_name' not in self.cleaned_data:
            return

        first_name = self.cleaned_data.get('first_name', '')

        return validate_name_field(first_name, self.language)

    def clean_last_name(self):
        """
        Validate the last name for valid characters.

        :return: Validated and formated last name.
        :rtype: str

        :raises forms.ValidationError: If the last name contains invalid
                                       characters.
        """
        if 'last_name' not in self.cleaned_data:
            return

        last_name = self.cleaned_data.get('last_name')

        return validate_name_field(last_name, self.language)

    def clean_phone_number(self):
        """
        Validate the phone number format to ensure it contains only digits
        and an optional '+' for international numbers.
        Also format the phone number to remove spaces, dashes, and parentheses.

        :return: Validated and formatted phone number.
        :rtype: str

        :raises forms.ValidationError: If the phone number format is invalid,
                                       if an international number does not have
                                       enough digits, or if a local number does
                                       not meet the minimum digit requirement.
        """
        if 'phone_number' not in self.cleaned_data:
            return

        phone_number = self.cleaned_data.get('phone_number')

        if phone_number:
            return validate_phone_number(phone_number, self.language)

        return phone_number

    def clean_date_of_birth(self):
        """
        Validate the date of birth to ensure it's in a valid format
        and not in the future or too old.

        :return: Validated date of birth.
        :rtype: datetime
        """
        if 'date_of_birth' not in self.cleaned_data:
            return

        date_of_birth = self.cleaned_data.get("date_of_birth")

        if date_of_birth:
            return validate_date_of_birth(date_of_birth, self.language)

        return date_of_birth

    def _update_field_attributes(self):
        """
        Update placeholders and labels for form fields
        based on translation keys.
        """
        for field_name, field in self.fields.items():
            # Set placeholder
            placeholder_key = f"enter_{field_name}"
            if placeholder_key in self.transl:
                field.widget.attrs.update(
                    {'placeholder': self.transl[placeholder_key]}
                )

            # Set label
            label_key = f"label_{field_name}"
            if label_key in self.transl:
                field.label = self.transl[label_key]

    def _update_error_messages(self):
        """
        Update error messages for validation based on translations.
        """
        if hasattr(self, 'error_messages'):
            self.error_messages.update({
                key: self.transl[key] for key in self.error_messages
                if key in self.transl
            })


class UserRegistrationForm(BaseUserForm, UserCreationForm):
    """
    Form for registering a new user.
    Includes fields for username, email, first name, last name, and password.

    :param language: Language code for translations (default: 'en').
    :type language: str
    """
    username = forms.CharField(max_length=100, required=True)
    email = forms.CharField(max_length=100, required=True,
                            widget=forms.EmailInput())
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    password1 = forms.CharField(max_length=50, required=True,
                                widget=forms.PasswordInput())
    password2 = forms.CharField(max_length=50, required=True,
                                widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name',
                  'password1', 'password2']

    def clean(self):
        """
        Validate the password fields to ensure they meet security requirements.

        :return: Cleaned data with validated passwords.
        :rtype: dict

        :raises forms.ValidationError: If password validation fails.
        """
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        try:
            validate_passwords(password1, password2, language=self.language)
        except forms.ValidationError as e:
            for error in e.messages:
                self.add_error('password1', error)
                self.add_error('password2', error)

        return cleaned_data


class UserLoginForm(BaseUserForm, AuthenticationForm):
    """
    Form for user login, supporting authentication via username or email.

    :param language: Language code for translations (default: 'en').
    :type language: str
    """
    username_or_email = forms.CharField(max_length=100, required=True)
    password = forms.CharField(max_length=50, required=True,
                               widget=forms.PasswordInput())

    class Meta:
        fields = ['username_or_email', 'password']

    def __init__(self, *args, **kwargs):
        """
        Initialize the form and remove the default username field.

        :param args: Positional arguments passed to the form constructor.
        :type args: tuple
        :param kwargs: Keyword arguments passed to the form constructor.
        :type kwargs: dict
        """
        super().__init__(*args, **kwargs)
        if 'username' in self.fields:
            self.fields.pop('username')  # Remove default username field
        self.fields = {
            'username_or_email': self.fields['username_or_email'],
            'password': self.fields['password'],
        }

    def clean_username_or_email(self):
        """
        Validate if the provided username or email exists in the system.

        :return: Validated username or email.
        :rtype: str

        :raises forms.ValidationError: If the input is not valid
                                       or does not match any user.
        """
        username_or_email = self.cleaned_data.get('username_or_email')

        try:
            if '@' in username_or_email:
                validate_email_format(username_or_email, self.language)
            else:
                validate_username_format(username_or_email, self.language)
        except forms.ValidationError as e:
            self.add_error('username_or_email', e)

        return username_or_email

    def clean(self):
        """
        Validate the login credentials and authenticate the user.

        :return: Cleaned data with authentication result.
        :rtype: dict

        :raises forms.ValidationError: If credentials are invalid
                                       or account is inactive
        """
        cleaned_data = super().clean()
        username_or_email = cleaned_data.get('username_or_email')
        password = cleaned_data.get('password')

        if username_or_email and password:
            user = (
                User.objects.filter(username=username_or_email).first()
                or User.objects.filter(email=username_or_email).first()
            )

            if not user or not authenticate(
                username=user.username, password=password
            ):
                self.add_error('password', self.transl["invalid_credentials"])
            elif not user.is_active:
                self.add_error(None, self.transl['inactive_account'])

            self.user_cache = user

        return cleaned_data

    def get_user(self):
        """
        Retrieve the authenticated user.

        :return: Authenticated user instance.
        :rtype: User
        """
        return self.user_cache


class UpdateUserProfileDataForm(BaseUserForm, forms.ModelForm):
    """
    Form for updating a user's personal data.
    """

    email = forms.CharField(
        required=False,
        widget=forms.EmailInput(),
    )
    date_of_birth = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'type': 'date'}),
    )

    class Meta:
        model = Profile
        fields = [
            'first_name', 'last_name', 'gender', 'date_of_birth',
            'phone_number', 'email', 'address', 'bio'
        ]
        widgets = {
            'first_name': forms.TextInput(),
            'last_name': forms.TextInput(),
            'gender': forms.Select(),
            'phone_number': forms.TextInput(),
            'address': forms.Textarea(attrs={'rows': 2}),
            'bio': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        """
        Initialize the form and set translation based on the language.

        This method retrieves the user's language setting and assigns
        the corresponding translation dictionary.

        :param args: Positional arguments passed to the form constructor.
        :type args: tuple
        :param kwargs: Keyword arguments passed to the form constructor.
        :type kwargs: dict
        """
        super().__init__(*args, **kwargs)

        # Translate gender options based on the selected language
        self.fields['gender'].choices = [
            ('', self.transl['choose_gender']),
            ('male', self.transl['male']),
            ('female', self.transl['female']),
            ('other', self.transl['other']),
        ]

    def clean_email(self):
        """
        Validate the uniqueness of the email and ensure it cannot be deleted.

        :return: Validated email.
        :rtype: str

        :raises forms.ValidationError: If the email is invalid, already exists,
                                    or is missing.
        """
        email = self.cleaned_data.get('email')

        # Check if email is present in the data
        if not email:
            raise forms.ValidationError(self.transl["email_required"])

        # Validity of the email format
        validate_email_format(email, self.language)

        # Check for uniqueness among active users
        if (
            User.objects.filter(email=email, is_active=True)
            .exclude(pk=self.instance.user.pk)
            .exists()
        ):
            raise forms.ValidationError(self.transl["email_exists"])

        return email


class CustomClearableFileInput(forms.ClearableFileInput):
    """
    Custom file input widget to style file input fields
    and provide an option to clear the uploaded file.

    This widget adds a 'custom-file-input' class to the file input field
    and handles the rendering of the clearable file field.
    """

    def __init__(self, *args, **kwargs):
        """Set default class for styling the file input"""
        kwargs.setdefault('attrs', {})['class'] = 'custom-file-input'
        super().__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, renderer=None):
        """
        Render the file input widget with the custom styles
        and handle the file clearing logic.

        :param name: The name attribute for the input field.
        :type name: str
        :param value: The current value of the field.
        :type value: str or None
        :param attrs: HTML attributes for the widget (optional).
        :type attrs: dict, optional
        :param renderer: The renderer to use for rendering (optional).
        :type renderer: callable, optional

        :return: The rendered HTML of the file input widget.
        :rtype: str
        """
        if value and hasattr(value, 'url'):
            value = None  # Reset the file value if the file has a URL
        return super().render(name, value, attrs, renderer)


class UpdateUserProfileAvatarForm(BaseUserForm, forms.ModelForm):
    """
    Form for updating a user's profile image (avatar).

    This form allows users to upload a new avatar image or remove
    the current avatar. It includes a custom file input widget
    and a boolean field to indicate avatar removal.
    """

    remove_avatar = forms.BooleanField(required=False)

    class Meta:
        model = Profile
        fields = ['avatar', 'remove_avatar']
        widgets = {
            'avatar': CustomClearableFileInput(),  # Use the custom file widget
        }

    def __init__(self, *args, **kwargs):
        """
        Initialize the form and set translation based on the language.

        :param args: Positional arguments passed to the form constructor.
        :type args: tuple
        :param kwargs: Keyword arguments passed to the form constructor.
        :type kwargs: dict
        """
        super().__init__(*args, **kwargs)

    def clean_avatar(self):
        """
        Validate and process the profile image uploaded by the user.

        This method performs the following checks:
        - Ensures an avatar is provided if 'remove_avatar' is not selected.
        - Validates the file format to be either PNG, JPG, or JPEG.
        - Verifies the image file's validity for Cloudinary resources
          or local files.

        :return: The validated profile image file or None if no image
                 is selected and remove_avatar is checked.
        :raises forms.ValidationError: If validation fails due to an empty
                                       file, unsupported format, or invalid
                                       image file.
        """
        avatar = self.cleaned_data.get('avatar')

        # Ensure avatar is provided if 'remove_avatar' is not selected
        if not avatar and not self.cleaned_data.get('remove_avatar', False):
            raise forms.ValidationError(self.transl["avatar_required"])

        if avatar:
            # Check if the file is empty
            if hasattr(avatar, 'size') and avatar.size == 0:
                raise forms.ValidationError(self.transl["avatar_empty"])

            # Check the file format (PNG, JPG, or JPEG).
            if hasattr(avatar, 'name') and avatar.name:
                if not avatar.name.lower().endswith(
                    ('.png', '.jpg', '.jpeg', 'webp')
                ):
                    raise forms.ValidationError(
                        self.transl["invalid_image_format"]
                    )
            else:
                # If the avatar file is missing or invalid, raise an error.
                raise forms.ValidationError(self.transl["avatar_required"])

            # For Cloudinary resources, download and validate the image
            if hasattr(avatar, 'url'):
                try:
                    avatar_file = avatar.download()  # Download image content
                    img = Image.open(io.BytesIO(avatar_file))
                except Exception:
                    raise forms.ValidationError(self.transl["avatar_invalid"])
            else:
                # Verify the file's validity for local uploads
                try:
                    img = Image.open(avatar)
                    img.verify()  # Check that this is a valid image file
                except (IOError, SyntaxError):
                    raise forms.ValidationError(self.transl["avatar_invalid"])

        return avatar

    def save(self, commit=True):
        """
        Save the profile changes, removing the avatar if requested.

        If 'remove_avatar' is selected, the avatar field is set to None
        before saving.

        :param commit: Whether to save the changes to the database.
        :type commit: bool
        :return: The updated profile instance.
        :rtype: Profile
        """
        profile = super().save(commit=False)

        # Set avatar to None if 'remove_avatar' is selected
        if self.cleaned_data.get('remove_avatar', False):
            profile.avatar = None

        # Save the profile with the updated data.
        if commit:
            profile.save()

        return profile


class PasswordChangeForm(BaseUserForm, forms.Form):
    """
    Form for updating user's password with fields for current password,
    new password, and password confirmation.
    """
    current_password = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.PasswordInput(),
    )
    new_password1 = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.PasswordInput(),
    )
    new_password2 = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.PasswordInput(),
    )

    def __init__(self, *args, **kwargs):
        """
        Initialize the form and set the user and translation
        based on the language.

        :param args: Positional arguments passed to the form constructor.
        :type args: tuple
        :param kwargs: Keyword arguments passed to the form constructor.
        :type kwargs: dict
        :param user: The user object for password validation.
        :type user: User
        :param language: The language code for translations (default is 'en').
        :type language: str
        """
        self.user = kwargs.get('user')  # Store the user object
        if 'user' in kwargs:
            kwargs.pop('user')  # Remove user from kwargs
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        """
        Validate the current password.

        :return: The validated current password.
        :rtype: str
        :raises forms.ValidationError: If the current password is incorrect.
        """
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise forms.ValidationError(
                self.transl['incorrect_current_password']
            )
        return current_password

    def clean(self):
        """
        Validate new passwords and check that they match.

        The new passwords are validated to ensure they meet the security
        criteria and that the two entered passwords match.

        :return: The validated cleaned data.
        :rtype: dict
        :raises forms.ValidationError: If the new passwords do not match
                                       or do not meet criteria.
        """
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')

        # Use custom validator to check passwords
        try:
            validate_passwords(
                new_password1, new_password2, language=self.language
            )
        except forms.ValidationError as e:
            for error in e.messages:
                self.add_error('new_password2', error)

        return cleaned_data


class CustomPasswordResetForm(PasswordResetForm):
    """
    Custom form for password reset that allows users to enter either a username
    or email to identify their account.
    """

    username_or_email = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'autofocus': True})
    )

    def __init__(self, *args, **kwargs):
        """
        Initialize the form and set translation based on the language.

        :param args: Positional arguments passed to the form constructor.
        :type args: tuple
        :param kwargs: Keyword arguments passed to the form constructor.
        :type kwargs: dict
        """
        self.lan = kwargs.pop('language', 'en')
        self.transl = translations.get(self.lan, translations['en'])
        super().__init__(*args, **kwargs)

        # Remove the default email field from the form
        self.fields.pop('email', None)

        # Update placeholder attributes for the field based on language setting
        self.fields['username_or_email'].widget.attrs.update({
            'placeholder': self.transl['enter_username_or_email'],
        })

    def clean_username_or_email(self):
        """
        Validate if the provided username or email exists in the system.
        If username is entered, retrieve the associated email.

        :return: Validated username or email.
        :rtype: str
        :raises forms.ValidationError: If neither a matching email nor
                                       username is found, or if the input
                                       format is invalid.

        """
        username_or_email = self.cleaned_data.get('username_or_email')

        # Regular expression for emails
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        # Regular expression for usernames
        username_regex = r'^[a-zA-Z0-9_-]+$'

        # Check if the input is an email or a username
        if '@' in username_or_email:
            if not re.match(email_regex, username_or_email):
                raise forms.ValidationError(
                    self.transl["invalid_email_format"]
                )
            # Validate email and get the associated user
            user = User.objects.filter(email=username_or_email).first()
        else:
            if not re.match(username_regex, username_or_email):
                raise forms.ValidationError(
                    self.transl["invalid_username_format"]
                )
            # Validate username and get the associated user
            user = User.objects.filter(username=username_or_email).first()

        # Raise validation error if no user is found
        if not user:
            raise forms.ValidationError(
                self.transl["password_reset_no_account"]
            )

        # If it's a username, return the associated email
        if '@' not in username_or_email:
            username_or_email = user.email

        return username_or_email


class CustomSetPasswordForm(SetPasswordForm):
    """
    Custom form for setting a new password.
    """

    new_password1 = forms.CharField(max_length=50, required=True,
                                    widget=forms.PasswordInput())
    new_password2 = forms.CharField(max_length=50, required=True,
                                    widget=forms.PasswordInput())

    def __init__(self, *args, **kwargs):
        """
        Initialize the form and set translation based on the language.

        :param args: Positional arguments passed to the form constructor.
        :type args: tuple
        :param kwargs: Keyword arguments passed to the form constructor.
        :type kwargs: dict
        """
        self.lan = kwargs.pop('language', 'en')
        self.transl = translations.get(self.lan, translations['en'])
        super().__init__(*args, **kwargs)

        # Update placeholder attributes for fields based on language setting
        self.fields['new_password1'].widget.attrs.update({
            'placeholder': self.transl['enter_new_password'],
        })
        self.fields['new_password2'].widget.attrs.update({
            'placeholder': self.transl['enter_confirm_new_password'],
        })

    def clean(self):
        """
        Perform custom password validation to ensure passwords meet security
        requirements and check for format compliance and matching.

        :return: Cleaned data with validated password fields.
        :rtype: dict
        :raises forms.ValidationError: If the passwords are invalid
                                       or do not match.
        """
        cleaned_data = super().clean()
        password1 = cleaned_data.get("new_password1")
        password2 = cleaned_data.get("new_password2")

        # If passwords are empty, fill them from raw data (POST data)
        if not password1 or not password2:
            password1 = self.data.get("new_password1", '')
            password2 = self.data.get("new_password2", '')

            # Manually add the passwords to cleaned_data
            cleaned_data['new_password1'] = password1
            cleaned_data['new_password2'] = password2

        # Manual check for empty fields
        if not password1 or not password2:
            raise forms.ValidationError(self.transl['password_required'])

        # Perform custom password validation
        try:
            validate_passwords(password1, password2, language=self.lan)
        except forms.ValidationError as e:
            for error in e.messages:
                self.add_error('new_password1', error)
                self.add_error('new_password2', error)

        return cleaned_data
