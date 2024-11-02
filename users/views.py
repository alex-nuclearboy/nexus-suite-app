from django.views import View
from django.shortcuts import render, redirect
from django.utils import timezone
from asgiref.sync import sync_to_async
import pytz

from newsapp.utils.utils import (
    get_translated_day_and_month, get_language, set_timezone
)
from .utils.translations import translations

from .forms import RegisterForm


class BaseUserView(View):
    """
    Base class view that includes common context setup, like date, time,
    and translations, to be used across various views.
    """
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

        return {
            'language': language,
            'translations': transl,
            'current_date': current_date,
            'current_time': current_time,
            'user_timezone': user_timezone,
        }


class SignupUserView(BaseUserView):
    """
    Asynchronous view for handling user signup, utilizing the BaseUserView to
    inherit shared context and common utilities.
    """
    form_class = RegisterForm
    template_name = 'users/signup.html'
    success_url = 'newsapp:index'

    async def get(self, request):
        """
        Handles GET requests for displaying the signup form.

        Parameters:
        request: HTTP GET request object.

        Returns:
        HTTPResponse: Rendered signup form with common context.
        """
        is_authenticated = await sync_to_async(
            lambda: request.user.is_authenticated
        )()
        if is_authenticated:
            # Redirect authenticated users to the main page
            return redirect(self.success_url)

        # Prepare the form and get common context
        form = self.form_class(
            language=await sync_to_async(get_language)(request)
        )
        context = await self.get_common_context(request)
        context["form"] = form

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
        is_authenticated = await sync_to_async(
            lambda: request.user.is_authenticated
        )()
        if is_authenticated:
            # Redirect authenticated users to the main page
            return redirect(self.success_url)

        # Initialize the form with POST data
        form = self.form_class(
            request.POST, language=await sync_to_async(get_language)(request)
        )

        if await sync_to_async(form.is_valid)():
            # Save the form and redirect on success
            await sync_to_async(form.save)()
            return redirect(self.success_url)

        # If the form is invalid, re-render the form with errors
        context = await self.get_common_context(request)
        context["form"] = form
        return render(request, self.template_name, context)
