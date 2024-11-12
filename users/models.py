from django.db import models
from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile

import cloudinary
import cloudinary.api
import cloudinary.uploader
from cloudinary.models import CloudinaryField

from PIL import Image
from io import BytesIO


class Profile(models.Model):
    """
    Represents a user profile containing personal data, with optional fields
    for avatar, gender, date of birth, phone number, address, and bio.

    :param user: A one-to-one relationship with the User model.
    :param first_name: The user's first name, optional.
    :param last_name: The user's last name, optional.
    :param gender: The user's gender, optional (choices: male, female, other).
    :param date_of_birth: The user's date of birth, optional.
    :param phone_number: The user's phone number, optional.
    :param email: The user's email, optional.
    :param address: The user's address, optional.
    :param bio: A short biography of the user, optional.
    :param avatar: The user's avatar image stored in Cloudinary,
                   with a default if none is provided.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[
            ('male', 'Male'), ('female', 'Female'), ('other', 'Other')
        ],
        blank=True,
        null=True
    )
    date_of_birth = models.DateField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    avatar = CloudinaryField(
        'image',
        default='nexussuiteapp/profile_images/default_avatar_a1kzyk.png',
        folder='nexussuiteapp/profile_images',
        blank=True,
    )

    def __str__(self):
        """
        Return a string representation of the Profile instance.

        Concatenates the user's first and last name along with their username.

        :return: A string containing the user's full name and username.
        :rtype: str
        """
        return f"{self.user.username} ({self.first_name} {self.last_name})"

    def save(self, *args, **kwargs):
        """
        Save the profile instance, handling avatar upload
        and updating the user's profile.

        This method handles any logic before saving the Profile instance,
        such as managing avatar updates and processing additional fields,
        if necessary.

        :param args: Positional arguments passed to the save method.
        :type args: tuple
        :param kwargs: Keyword arguments passed to the save method.
        :type kwargs: dict

        :return: Saves the profile data with avatar and personal information.
        :rtype: None
        """

        # Check if avatar is a newly uploaded image (InMemoryUploadedFile)
        if isinstance(self.avatar, InMemoryUploadedFile):
            # Resize the image if it's larger than 250x250
            image = Image.open(self.avatar)
            if image.width > 250 or image.height > 250:
                image.thumbnail((250, 250), Image.Resampling.LANCZOS)
                output = BytesIO()
                img_format = (
                    'PNG' if 'png' in self.avatar.name.lower() else 'JPEG'
                )
                image.save(output, format=img_format)
                output.seek(0)  # Reset file pointer to the start

                # Upload the resized image to Cloudinary and save the URL
                cloudinary_response = cloudinary.uploader.upload(
                    output, folder='nexussuiteapp/profile_images'
                )
                relative_url = (
                    cloudinary_response['secure_url'].split('upload/')[-1]
                )
                self.avatar = f"image/upload/{relative_url}"

        # Save the profile instance with updated avatar and personal details
        super().save(*args, **kwargs)
