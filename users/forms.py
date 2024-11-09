from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import (
    UserCreationForm, AuthenticationForm
)

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import (
    validate_password,
    get_default_password_validators
)

from .models import Profile
from .utils.translations import translations


def validate_passwords(password1, password2, language='en'):
    """
    Custom password validator that checks if passwords match
    and follow the required format and complexity.
    """
    # Check for password matching
    if password1 and password2 and password1 != password2:
        raise forms.ValidationError(
            translations.get(language, translations['en'])['password_mismatch']
        )

    # Check the password format
    try:
        validate_password(
                    password1,
                    password_validators=get_default_password_validators()
                )
    except forms.ValidationError as e:
        error_messages = []
        for message in e.messages:
            # Map each error to a translated message if available
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
                error_messages.append(message)

        if error_messages:
            raise forms.ValidationError(error_messages)


class UserRegistrationForm(UserCreationForm):
    """
    Form for registering a new user.
    Includes additional fields for email, first name, and last name.
    """
    username = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(max_length=100, required=False)
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

    def __init__(self, *args, **kwargs):
        """
        Initialize the form and set translation based on the language.
        """
        self.lan = kwargs.pop('language', 'en')
        self.transl = translations.get(self.lan, translations['en'])

        super().__init__(*args, **kwargs)

        # Update placeholder attributes for fields
        self.fields['username'].widget.attrs.update({
            'placeholder': self.transl['enter_username'],
            'autofocus': True,
        })
        self.fields['email'].widget.attrs.update({
            'placeholder': self.transl['enter_email'],
        })
        self.fields['first_name'].widget.attrs.update({
            'placeholder': self.transl['enter_first_name'],
        })
        self.fields['last_name'].widget.attrs.update({
            'placeholder': self.transl['enter_last_name'],
        })
        self.fields['password1'].widget.attrs.update({
            'placeholder': self.transl['enter_password'],
        })
        self.fields['password2'].widget.attrs.update({
            'placeholder': self.transl['enter_password_conf'],
        })

        # Update error messages for validation
        self.error_messages.update({
            'username_exists': self.transl['username_exists'],
            'email_exists': self.transl['email_exists'],
            'password_mismatch': self.transl['password_mismatch'],
            'password_too_short': self.transl['password_too_short'],
            'password_too_common': self.transl['password_too_common'],
            'password_entirely_numeric': self.transl[
                'password_entirely_numeric'
            ],
        })

    def clean_username(self):
        """
        Validate that the username is unique.
        """
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(self.transl["username_exists"])
        return username

    def clean_email(self):
        """
        Validate that the email is unique.
        """
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError(self.transl["email_exists"])
        return email

    def clean(self):
        """
        Override clean method to use custom password validator.
        """
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        # Use custom validator to check passwords
        try:
            validate_passwords(password1, password2, language=self.lan)
        except forms.ValidationError as e:
            for error in e.messages:
                self.add_error('password1', error)
                self.add_error('password2', error)

        return cleaned_data


class UserLoginForm(AuthenticationForm):
    """
    Form for user login, allowing authentication via username or email.
    """
    username_or_email = forms.CharField(max_length=100, required=True)
    password = forms.CharField(max_length=50, required=True,
                               widget=forms.PasswordInput())

    class Meta:
        fields = ['username_or_email', 'password']

    def __init__(self, *args, **kwargs):
        """
        Initialize the form and set translation based on the language.
        """
        self.lan = kwargs.pop('language', 'en')
        self.transl = translations.get(self.lan, translations['en'])

        super().__init__(*args, **kwargs)

        self.fields.pop('username', None)  # Remove default username field

        # Update placeholder attributes for fields
        self.fields['username_or_email'].widget.attrs.update({
            'placeholder': self.transl['enter_username_or_email'],
            'autofocus': True,
        })
        self.fields['password'].widget.attrs.update({
            'placeholder': self.transl['enter_password'],
        })

    def clean_username_or_email(self):
        """
        Validate if the provided username or email exists.
        """
        username_or_email = self.cleaned_data.get('username_or_email')

        if '@' in username_or_email:
            user = User.objects.filter(email=username_or_email).first()
        else:
            user = User.objects.filter(username=username_or_email).first()

        if not user:
            raise forms.ValidationError(self.transl["invalid_credentials"])

        return username_or_email

    def clean(self):
        """
        Validate the login credentials and authenticate the user.
        """
        cleaned_data = super().clean()
        username_or_email = cleaned_data.get('username_or_email')
        password = cleaned_data.get('password')

        if username_or_email and password:
            user = User.objects.filter(username=username_or_email).first() or \
                   User.objects.filter(email=username_or_email).first()

            if not user or not authenticate(
                username=user.username, password=password
            ):
                raise forms.ValidationError(self.transl["invalid_credentials"])

            self.user_cache = user

            if not self.user_cache.is_active:
                raise forms.ValidationError(
                    self.transl['inactive_account'], code='inactive'
                )

        return cleaned_data

    def get_user(self):
        """
        Retrieve the authenticated user.
        """
        return self.user_cache


class ProfileUpdateForm(forms.ModelForm):
    """
    Form for updating a user's profile with fields for first name,
    last name, and avatar image.
    """
    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'avatar']
        widgets = {
            'first_name': forms.TextInput(),
            'last_name': forms.TextInput(),
            'avatar': forms.ClearableFileInput(),
        }

    def __init__(self, *args, **kwargs):
        """
        Initialize the form with language-based messages.
        """
        self.lan = kwargs.pop('language', 'en')
        self.transl = translations.get(self.lan, translations['en'])
        super().__init__(*args, **kwargs)

    def clean_avatar(self):
        """
        Validate that the uploaded file is an image in an acceptable format.
        """
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            if not avatar.name.lower().endswith(('.png', '.jpg', '.jpeg')):
                raise forms.ValidationError(
                    self.transl["invalid_image_format"]
                )
        return avatar

    def clean(self):
        """
        Ensure that an avatar is uploaded when creating a new profile.
        """
        cleaned_data = super().clean()
        avatar = cleaned_data.get("avatar")

        # Make sure avatar is provided for new profile, if it's not set yet
        if not avatar and self.instance.pk is None:
            raise forms.ValidationError(
                self.transl["required_field"],
            )

        return cleaned_data
