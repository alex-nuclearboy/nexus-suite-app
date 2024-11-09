from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Creates or updates a user's profile when a user is saved.

    Parameters:
        sender (Model): The model that sent the signal (User).
        instance (User): The instance of the model (the user being saved).
        created (bool): Boolean flag indicating whether the user was created.
        **kwargs: Arbitrary keyword arguments.

    This signal performs two operations:
        - If a new user is created, it creates a new Profile
          associated with the user.
        - If the user is updated (but not created),
          it updates the associated Profile's first and last name.
    """
    if created:
        # Create a new profile when a new user is created
        Profile.objects.create(
            user=instance,
            first_name=instance.first_name,
            last_name=instance.last_name
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
                last_name=instance.last_name
            )
        profile.first_name = instance.first_name
        profile.last_name = instance.last_name
        profile.save()
