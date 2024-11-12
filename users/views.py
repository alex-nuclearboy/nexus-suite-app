from django.views.generic import TemplateView
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.shortcuts import render, redirect

from cloudinary.exceptions import Error as CloudinaryError

import pytz

from newsapp.utils.utils import (
    get_translated_day_and_month, get_language, set_timezone
)
from .utils.translations import translations

from .forms import (
    UserRegistrationForm, UserLoginForm,
    UpdateUserProfileDataForm, UpdateUserProfileAvatarForm,
    PasswordChangeForm
)


class BaseUserView(TemplateView):
    """
    Base class for handling user-related requests. Provides common methods
    for retrieving user data, checking authentication, and setting shared
    context for various views.

    Methods:
    - get_user: Retrieve the user from the current request.
    - is_authenticated: Check if the user is authenticated.
    - get_common_context: Gather shared context data for rendering templates.
    """

    def get_user(self, request):
        """
        Returns the user from the current request.

        :param request: The user request.
        :type request: HttpRequest
        :return: The user from the request.
        :rtype: User
        """
        return request.user

    def is_authenticated(self, request):
        """
        Checks if the user is authenticated.

        :param request: The user request.
        :type request: HttpRequest
        :return: True if the user is authenticated, otherwise False.
        :rtype: bool
        """
        return request.user.is_authenticated

    def get_avatar_url(self, user):
        """
        Retrieves the avatar URL for the user, if available.

        :param user: The user object.
        :type user: User
        :return: The avatar URL or None if no avatar is set.
        :rtype: Optional[str]
        """
        if (
            user.is_authenticated
                and hasattr(user, 'profile')
                and user.profile.avatar
        ):
            return user.profile.avatar.url
        return None

    def get_common_context(self, request):
        """
        Constructs shared context for all user views, including current time,
        date, and language-specific translations.

        :param request: The user request.
        :type request: HttpRequest
        :return: A dictionary containing context data for the template.
        :rtype: dict
        """
        language = get_language(request)
        transl = translations.get(language, translations['en'])

        set_timezone(request)

        # Retrieve user timezone and current time
        timezone_str = request.session.get('django_timezone', 'UTC')
        user_timezone = pytz.timezone(timezone_str)
        now = timezone.now().astimezone(user_timezone)

        # Translate the date and time
        translated_day, translated_month = get_translated_day_and_month(
            now, language, 'full'
        )
        current_time = now.strftime('%H:%M')
        current_date = (
            f"{translated_day}, {now.day} {translated_month} {now.year}"
        )

        # Retrieve user's avatar URL
        user = self.get_user(request)
        avatar_url = self.get_avatar_url(request.user)

        return {
            'language': language,
            'translations': transl,
            'current_date': current_date,
            'current_time': current_time,
            'user_timezone': user_timezone,
            'user': user,
            'avatar_url': avatar_url,
            'is_authenticated': self.is_authenticated(request),
        }


class SignupUserView(BaseUserView):
    """
    Handles user registration.

    Processes:
    - GET: Renders the registration form.
    - POST: Validates and saves the user.

    Uses:
    - UserRegistrationForm: Form used to register a new user.
    - translations: For displaying language-specific messages.
    """

    form_class = UserRegistrationForm
    template_name = 'users/signup.html'
    success_url = 'users:login'

    def get(self, request):
        """
        Handles GET request to render the registration form.

        :param request: The user request.
        :type request: HttpRequest
        :return: Template with the registration form.
        :rtype: HttpResponse
        """
        # Check if the user is already authenticated
        if self.is_authenticated(request):
            # Redirect authenticated users to the success page
            return redirect(self.success_url)

        # Initialize the registration form with the current language
        form = self.form_class(language=get_language(request))
        # Prepare the context with common data and the form
        context = self.get_common_context(request)
        context.update({
            "form": form,
            "form_errors": form.errors
        })

        return render(request, self.template_name, context)

    def post(self, request):
        """
        Handles POST request to process the registration form
        and create a user.

        :param request: The user request with form data.
        :type request: HttpRequest
        :return: Redirects to the login page after successful registration.
        :rtype: HttpResponse
        """
        # Check if the user is already authenticated
        if self.is_authenticated(request):
            # Redirect authenticated users to the success page
            return redirect(self.success_url)

        # Initialize the form with POST data and the current language
        language = get_language(request)
        transl = translations.get(language, translations['en'])
        form = self.form_class(request.POST, language=language)

        # Check if the form is valid
        if form.is_valid():
            # Save the form and redirect on success
            form.save()
            messages.success(request, transl['signup_success'])
            return redirect(self.success_url)

        # If the form is invalid, re-render the form with errors
        context = self.get_common_context(request)
        context.update({
            "form": form,
            "form_errors": form.errors
        })

        return render(request, self.template_name, context)


class LoginUserView(BaseUserView):
    """
    Handles user login.

    Processes:
    - GET: Renders the login form.
    - POST: Validates the login form and logs in the user.

    Uses:
    - UserLoginForm: Form for log in a user.
    - translations: For displaying language-specific messages.
    """

    form_class = UserLoginForm
    template_name = 'users/login.html'
    success_url = 'newsapp:index'

    def get(self, request):
        """
        Handles GET request to render the login form.

        :param request: The user request.
        :type request: HttpRequest
        :return: Template with the login form.
        :rtype: HttpResponse
        """
        # Check if the user is already authenticated
        if self.is_authenticated(request):
            # Redirect authenticated users to the success page
            return redirect(self.success_url)

        # Initialize the login form with the current language
        form = self.form_class(language=get_language(request))
        # Prepare the context with common data and the form
        context = self.get_common_context(request)
        context.update({
            "form": form,
            "form_errors": form.errors
        })

        return render(request, self.template_name, context)

    def post(self, request):
        """
        Handles POST request to process the login form
        and authenticate the user.

        :param request: The user request with form data.
        :type request: HttpRequest
        :return: Redirects to the home page after successful login.
        :rtype: HttpResponse
        """
        # Check if the user is already authenticated
        if self.is_authenticated(request):
            # Redirect authenticated users to the success page
            return redirect(self.success_url)

        # Initialize the form with POST data and the current language
        language = get_language(request)
        transl = translations.get(language, translations['en'])
        form = self.form_class(request, data=request.POST, language=language)

        # Check if the form is valid
        if form.is_valid():
            user = form.get_user()
            if user is not None:
                login(request, user)
                messages.success(request, transl['login_success'])
                return redirect(self.success_url)
            else:
                messages.error(request, transl['invalid_credentials'])
        else:
            # Handle form validation errors
            for field in form:
                for error in field.errors:
                    messages.error(request, error)
            for error in form.non_field_errors():
                messages.error(request, error)

        # If form is invalid, re-render the login page with errors
        context = self.get_common_context(request)
        context.update({
            "form": form,
            "form_errors": form.errors
        })

        return render(request, self.template_name, context)


class LogoutUserView(BaseUserView):
    """
    Handles user logout.

    Processes:
    - GET: Logs out the user and redirects to the home page.

    Uses:
    - translations: For displaying language-specific messages.
    """

    success_url = 'newsapp:index'

    @method_decorator(login_required)
    def get(self, request):
        """
        Handles GET request to log the user out and redirect to the home page.

        :param request: The user request.
        :type request: HttpRequest
        :return: Redirects to the home page after logout.
        :rtype: HttpResponse
        """
        # Get the current language for translations
        language = get_language(request)
        transl = translations.get(language, translations['en'])

        # Log out the user
        logout(request)

        # Display a success message after logout
        messages.success(request, transl['logout_success'])
        request.session['language'] = language

        return redirect(self.success_url)


class UpdateUserProfileView(BaseUserView):
    """
    Handles user profile updates.

    Processes:
    - GET: Renders the user profile form.
    - POST: Validates and saves the updated user profile.

    Uses:
    - UpdateUserProfileDataForm: Form for editing user profile data.
    - UpdateUserProfileAvatarForm: Form for editing user avatar.
    - PasswordChangeForm: Form for changing user password.
    """

    template_name = 'users/profile.html'

    @method_decorator(login_required)
    def get(self, request):
        """
        Handles GET request to render the user profile form.

        :param request: The user request.
        :type request: HttpRequest
        :return: Template with the profile editing form.
        :rtype: HttpResponse
        """
        # Retrieve the user's profile
        profile = request.user.profile

        # Initialize the profile editing forms with current data
        data_form = UpdateUserProfileDataForm(
            instance=profile, language=get_language(request)
        )
        avatar_form = UpdateUserProfileAvatarForm(
            instance=profile, language=get_language(request)
        )
        password_form = PasswordChangeForm(
            user=request.user, language=get_language(request)
        )

        # Prepare the context with the forms
        context = self.get_common_context(request)
        context.update({
            'data_form': data_form,
            'avatar_form': avatar_form,
            'password_form': password_form,
        })
        return render(request, self.template_name, context)

    @method_decorator(login_required)
    def post(self, request):
        """
        Handles POST request to process profile update.

        :param request: The user request with form data.
        :type request: HttpRequest
        :return: Renders profile page with success message or form errors.
        :rtype: HttpResponse
        """
        # Get the current language and translations
        language = get_language(request)
        transl = translations.get(language, translations['en'])

        # Prepare the context with common data and user profile
        context = self.get_common_context(request)
        profile = request.user.profile

        # Handle avatar update
        if "update_avatar" in request.POST:
            avatar_form = UpdateUserProfileAvatarForm(
                request.POST, request.FILES, instance=profile,
                language=language
            )

            avatar = request.FILES.get('avatar')  # Access the uploaded avatar
            if avatar and not avatar.read():
                # Remove any existing errors for 'avatar'
                avatar_form.errors.pop('avatar', None)
                # If the file has no content
                avatar_form.add_error('avatar', transl['avatar_empty'])

            if avatar_form.is_valid():
                try:
                    avatar_form.save()
                    messages.success(request, transl['avatar_updated_success'])
                    return redirect('users:profile')
                except CloudinaryError as e:
                    error_message = transl['cloudinary_upload_failed'] + str(e)
                    avatar_form.add_error('avatar', error_message)
            # Update context with form and errors if applicable
            context.update({
                'avatar_form': avatar_form,
                'avatar_form_errors': avatar_form.errors
            })

        # Handle avatar removal
        elif "remove_avatar" in request.POST:
            profile.avatar = (
                'nexussuiteapp/profile_images/default_avatar_a1kzyk.png'
            )
            profile.save()
            messages.success(request, transl['avatar_removed_success'])
            return redirect('users:profile')

        # Handle personal data update
        elif "update_profile" in request.POST:
            data_form = UpdateUserProfileDataForm(
                request.POST, instance=profile,
                language=language
            )
            if data_form.is_valid():
                profile = data_form.save(commit=False)
                request.user.first_name = profile.first_name
                request.user.last_name = profile.last_name
                request.user.email = profile.email
                request.user.save()
                profile.save()
                messages.success(request, transl['profile_updated_success'])
                return redirect('users:profile')
            # Update context with form and errors if applicable
            context.update({
                'data_form': data_form,
                'data_form_errors': data_form.errors
            })

        # Handle password change
        elif "change_password" in request.POST:
            password_form = PasswordChangeForm(
                request.POST, user=request.user, language=language
            )
            if password_form.is_valid():
                new_password = password_form.cleaned_data['new_password1']
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, transl['password_changed_success'])
                return redirect('users:profile')
            # Update context with form and errors if applicable
            context.update({
                'password_form': password_form,
                'password_form_errors': password_form.errors
            })

        # If any of the forms failed validation,
        # return the context with error messages
        context.setdefault(
            'data_form',
            UpdateUserProfileDataForm(instance=profile, language=language)
        )
        context.setdefault(
            'avatar_form',
            UpdateUserProfileAvatarForm(instance=profile, language=language)
        )
        context.setdefault(
            'password_form',
            PasswordChangeForm(user=request.user, language=language)
        )

        return render(request, self.template_name, context)
