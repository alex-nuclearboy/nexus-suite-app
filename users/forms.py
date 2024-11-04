from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

from .utils.translations import translations


class RegisterForm(UserCreationForm):
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
        self.lan = kwargs.pop('language', 'en')
        self.transl = translations.get(self.lan, translations['en'])

        super(RegisterForm, self).__init__(*args, **kwargs)

        self.fields['username'].widget.attrs.update({
            'placeholder': self.transl['enter_username'],
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

        def clean_username(self):
            username = self.cleaned_data.get('username')
            if User.objects.filter(username=username).exists():
                raise forms.ValidationError(self.transl["username_exists"])
            return username

        def clean_email(self):
            email = self.cleaned_data.get('email')
            if email and User.objects.filter(email=email).exists():
                raise forms.ValidationError(self.transl["email_exists"])
            return email

        def clean_password2(self):
            password1 = self.cleaned_data.get('password1')
            password2 = self.cleaned_data.get('password2')
            if password1 and password2 and password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch']
                )
            return password2


class LoginForm(AuthenticationForm):
    username_or_email = forms.CharField(max_length=100, required=True)
    password = forms.CharField(max_length=50, required=True,
                               widget=forms.PasswordInput())

    class Meta:
        fields = ['username_or_email', 'password']

    def __init__(self, *args, **kwargs):
        self.lan = kwargs.pop('language', 'en')
        self.transl = translations.get(self.lan, translations['en'])

        super(LoginForm, self).__init__(*args, **kwargs)

        self.fields['username_or_email'].widget.attrs.update({
            'placeholder': self.transl['enter_username_or_email'],
        })
        self.fields['password'].widget.attrs.update({
            'placeholder': self.transl['enter_password'],
        })

    def clean(self):
        cleaned_data = super().clean()
        username_or_email = cleaned_data.get('username_or_email')
        password = cleaned_data.get('password')

        if username_or_email and password:
            user = authenticate(username=username_or_email, password=password)
            if user is None:
                raise forms.ValidationError(self.transl["invalid_credentials"])
        return cleaned_data
