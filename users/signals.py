from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Creates or updates a user's profile when a user is saved.

    This signal performs two operations:
        - If a new user is created, a new Profile is created and associated
          with the user.
        - If the user is updated (but not created), the associated Profile's
          first name, last name, and email are updated.

    :param sender: The model that sent the signal (User).
    :type sender: Model
    :param instance: The instance of the model (the user being saved).
    :type instance: User
    :param created: Boolean flag indicating whether the user was created.
    :type created: bool
    :param kwargs: Arbitrary keyword arguments.
    :type kwargs: dict
    :return: None
    """
    if created:
        # Create a new profile when a new user is created
        Profile.objects.create(
            user=instance,
            first_name=instance.first_name,
            last_name=instance.last_name,
            email=instance.email
        )
    else:
        # Update existing profile when user details change
        try:
            profile = instance.profile
        except Profile.DoesNotExist:
            # If profile does not exist, create one
            profile = Profile.objects.create(
                user=instance,
                first_name=instance.first_name,
                last_name=instance.last_name,
                email=instance.email
            )

        # Update profile fields if the user details have changed
        profile.first_name = instance.first_name
        profile.last_name = instance.last_name
        instance.profile.email = instance.email
        profile.save()
