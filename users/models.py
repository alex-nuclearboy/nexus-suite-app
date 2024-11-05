from django.db import models
from django.contrib.auth.models import User
from django.core.files.base import ContentFile

from cloudinary.models import CloudinaryField
from PIL import Image
from io import BytesIO


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    avatar = CloudinaryField(
        'image',
        default='nexussuiteapp/profile_images/default_avatar_a1kzyk.png',
        folder='profile_images'
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.user.username})"

    def save(self, *args, **kwargs):
        if self.avatar and not self._state.adding:
            # Save the instance before resizing
            super().save(*args, **kwargs)

            # Open the image to resize it
            img = Image.open(self.avatar)
            if img.height > 250 or img.width > 250:
                output = BytesIO()

                # Use Resampling.LANCZOS for high-quality downsampling
                img.thumbnail((250, 250), Image.Resampling.LANCZOS)

                # Determine the format based on the file extension
                img_format = (
                    'PNG' if 'png' in self.avatar.name.lower() else 'JPEG'
                )
                img.save(output, format=img_format)
                output.seek(0)

                # Save the resized image back to the avatar field
                self.avatar.save(
                    self.avatar.name,
                    ContentFile(output.getvalue()),
                    save=False
                )

            # Save the instance again after resizing
            super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)
