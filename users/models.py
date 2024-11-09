from django.db import models
from django.contrib.auth.models import User
from django.core.files.base import ContentFile

from cloudinary.models import CloudinaryField
import cloudinary
import cloudinary.api
from PIL import Image
from io import BytesIO
import requests


class Profile(models.Model):
    """
    A model representing a user profile.

    Parameters:
        user (OneToOneField): A one-to-one relationship with the User model.
        first_name (CharField): The user's first name, optional.
        last_name (CharField): The user's last name, optional.
        avatar (CloudinaryField): The user's avatar image stored in Cloudinary,
                                  with a default value if none is provided.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    avatar = CloudinaryField(
        'image',
        default='nexussuiteapp/profile_images/default_avatar_a1kzyk.png',
        folder='nexussuiteapp/profile_images'
    )

    def __str__(self):
        """
        Returns a string representation of the Profile instance.

        Returns:
            str: A string containing the user's full name and username.
        """
        return f"{self.user.username} ({self.first_name} {self.last_name})"

    def save(self, *args, **kwargs):
        """
        Saves the Profile instance, resizing the avatar image if necessary.

        This method overrides the default save method to ensure that the
        avatar image is resized to fit within a 250x250 pixel bounding box
        if it exceeds those dimensions.

        Parameters:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """

        if self.avatar and hasattr(self.avatar, 'public_id'):
            # Fetch and resize the avatar image if necessary
            result = cloudinary.api.resource(self.avatar.public_id)
            image_url = result.get('secure_url')

            # Fetch the image from Cloudinary
            response = requests.get(image_url)
            img = Image.open(BytesIO(response.content))

            # Resize image if it's too large
            if img.height > 250 or img.width > 250:
                output = BytesIO()
                img.thumbnail((250, 250), Image.Resampling.LANCZOS)
                img_format = (
                    'PNG' if 'png' in self.avatar.name.lower() else 'JPEG'
                )
                img.save(output, format=img_format)
                output.seek(0)

                # Save resized image back to Cloudinary
                self.avatar.save(
                    self.avatar.name,
                    ContentFile(output.getvalue()),
                    save=False
                )

        # Only save once after all updates are done
        super(Profile, self).save(*args, **kwargs)

    def update_user_name(self):
        """
        Updates the User model's first and last name fields.
        This method synchronizes the first and last name in the Profile model
        with the corresponding fields in the User model.
        """
        if self.first_name:
            self.user.first_name = self.first_name
        if self.last_name:
            self.user.last_name = self.last_name
        self.user.save()
