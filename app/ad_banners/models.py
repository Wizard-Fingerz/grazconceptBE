from django.db import models
from cloudinary.models import CloudinaryField  # <-- As instructed per file_context_0
import os

def ad_banner_image_upload_path(instance, filename):
    # This will upload to MEDIA_ROOT/ad_banners/<filename>
    return os.path.join('ad_banners', filename)

class AdBanner(models.Model):
    POSITION_CHOICES = [
        ('top', 'Top'),
        ('bottom', 'Bottom'),
        ('sidebar', 'Sidebar'),
        ('inline', 'Inline'),
    ]

    title = models.CharField(max_length=255)
    image = CloudinaryField('image', blank=True, null=True)  # Use CloudinaryField instead of ImageField
    link_url = models.URLField(max_length=500, blank=True, null=True)
    position = models.CharField(max_length=20, choices=POSITION_CHOICES, default='top')
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_currently_active(self):
        from django.utils import timezone
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True

    def __str__(self):
        return self.title
