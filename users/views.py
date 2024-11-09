from django.views import View
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from asgiref.sync import sync_to_async
import pytz

from newsapp.utils.utils import (
    get_translated_day_and_month, get_language, set_timezone
)
from .utils.translations import translations

from .forms import UserRegistrationForm, UserLoginForm


class BaseUserView(View):
    """
    Base class view that includes common context setup, like date, time,
    and translations, to be used across various views.
    """
    @sync_to_async
    def get_user(self, request):
        return request.user

    @sync_to_async
    def is_authenticated(self, request):
        return request.user.is_authenticated

    async def get_common_context(self, request):
        """
        Forms and returns a common context dictionary for all views.

        Parameters:
        request: User's session request object containing session data.

        Returns:
        dict: Dictionary with general data such as language, timezone,
              current date and time, and translations.
        """
        language = await sync_to_async(get_language)(request)
        transl = translations.get(language, translations['en'])

        await sync_to_async(set_timezone)(request)

        # Get user's timezone and current time
        timezone_str = (
            await sync_to_async(request.session.get)('django_timezone', 'UTC')
        )
        user_timezone = pytz.timezone(timezone_str)
        now = timezone.now().astimezone(user_timezone)

        # Translate the date and time
        translated_day, translated_month = (
            await sync_to_async(get_translated_day_and_month)(
                now, language, 'full'
            )
        )
        current_time = now.strftime('%H:%M')
        current_date = (
            f"{translated_day}, {now.day} {translated_month} {now.year}"
        )

        user = await self.get_user(request)

        return {
            'language': language,
            'translations': transl,
            'current_date': current_date,
            'current_time': current_time,
            'user_timezone': user_timezone,
            'user': user,
        }


class SignupUserView(BaseUserView):
    """
    Asynchronous view for handling user signup, using the BaseUserView to
    inherit shared context and common utilities.
    """
    form_class = UserRegistrationForm
    template_name = 'users/signup.html'
    success_url = 'users:login'

    async def get(self, request):
        """
        Handles GET requests for displaying the signup form.

        Parameters:
        request: HTTP GET request object.

        Returns:
        HTTPResponse: Rendered signup form with common context.
        """
        if await self.is_authenticated(request):
            # Redirect authenticated users to the main page
            return redirect(self.success_url)

        # Prepare the form and get common context
        form = self.form_class(
            language=await sync_to_async(get_language)(request)
        )
        context = await self.get_common_context(request)
        context["form"] = form
        context["form_errors"] = form.errors

        return render(request, self.template_name, context)

    async def post(self, request):
        """
        Handles POST requests for processing the signup form submission.

        Parameters:
        request: HTTP POST request object with form data.

        Returns:
        HTTPResponse: Redirects to the main page on successful signup,
                      otherwise re-renders the signup form with errors.
        """
        if await self.is_authenticated(request):
            # Redirect authenticated users to the main page
            return redirect(self.success_url)

        # Initialize the form with POST data
        form = self.form_class(
            request.POST, language=await sync_to_async(get_language)(request)
        )

        language = await sync_to_async(get_language)(request)
        transl = translations.get(language, translations['en'])

        if await sync_to_async(form.is_valid)():
            # Save the form and redirect on success
            await sync_to_async(form.save)()
            await sync_to_async(messages.success)(
                request, transl['signup_success']
            )
            return redirect(self.success_url)

        # If the form is invalid, re-render the form with errors
        context = await self.get_common_context(request)
        context["form"] = form
        context["form_errors"] = form.errors
        return render(request, self.template_name, context)


class LoginUserView(BaseUserView):
    """
    View for handling user login.
    """
    form_class = UserLoginForm
    template_name = 'users/login.html'
    success_url = 'newsapp:index'

    async def get(self, request):
        """
        Handles GET requests and displays the login form.

        Parameters:
        request: HTTP GET request object.

        Returns:
        HTTPResponse: Renders the login page with the form.
        """
        if await self.is_authenticated(request):
            # Redirect authenticated users to the main page
            return redirect(self.success_url)

        # Prepare the form and get common context asynchronously
        form = self.form_class(
            language=await sync_to_async(get_language)(request)
        )
        context = await self.get_common_context(request)
        context["form"] = form
        context["form_errors"] = form.errors

        return render(request, self.template_name, context)

    async def post(self, request):
        """
        Handles POST requests for user login.

        Parameters:
        request: HTTP POST request object.

        Returns:
        HTTPResponse: Redirects to the home page upon successful login,
                      otherwise re-renders the login page with errors.
        """
        language = await sync_to_async(get_language)(request)
        transl = translations.get(language, translations['en'])

        form = self.form_class(request, data=request.POST, language=language)

        if await sync_to_async(form.is_valid)():
            user = form.get_user()
            if user is not None:
                await sync_to_async(login)(request, user)
                await sync_to_async(messages.success)(request,
                                                      transl['login_success'])
                return redirect(self.success_url)
            else:
                await sync_to_async(messages.error)(
                    request, transl['invalid_credentials']
                )
        else:
            for field in form:
                for error in field.errors:
                    await sync_to_async(messages.error)(request, error)
            for error in form.non_field_errors():
                await sync_to_async(messages.error)(request, error)

        context = await self.get_common_context(request)
        context["form"] = form
        context["form_errors"] = form.errors

        return render(request, self.template_name, context)


class LogoutUserView(BaseUserView):
    """
    Asynchronous view for handling user logout.
    """

    @method_decorator(login_required)
    def get(self, request):
        """# Login by username
        Handles GET requests for logging out the user.

        Parameters:
        request: HTTP GET request object.

        Returns:
        HTTPResponse: Redirects to the home page after successful logout,
                      displaying a success message.
        """
        language = get_language(request)
        transl = translations.get(language, translations['en'])

        # Log out the user
        logout(request)

        # Display a success message
        messages.success(request, transl['logout_success'])
        request.session['language'] = language

        return redirect('newsapp:index')
