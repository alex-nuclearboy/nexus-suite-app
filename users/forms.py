from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

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
