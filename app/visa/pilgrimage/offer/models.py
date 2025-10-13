from django.db import models
from django_countries.fields import CountryField
from definition.models import TableDropDownDefinition
from account.client.models import Client  # For applicant ForeignKey

class PilgrimageOffer(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    pilgrimage_type = models.ForeignKey(
        TableDropDownDefinition,
        on_delete=models.PROTECT,
        limit_choices_to={'table_name': 'pilgrimage_type', 'is_active': True},
        related_name='pilgrimage_offers',
        help_text="Type of pilgrimage (e.g., Religious, Cultural, Historical, Other)"
    )
    destination = CountryField()
    city = models.CharField(max_length=100, blank=True, null=True, help_text="City of the pilgrimage destination")
    start_date = models.DateField()
    end_date = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total price if not sponsored or for the non-sponsored portion")
    currency = models.CharField(max_length=10, default="USD")
    sponsorship = models.ForeignKey(
        TableDropDownDefinition,
        on_delete=models.PROTECT,
        limit_choices_to={'table_name': 'pilgrimage_sponsorship_type', 'is_active': True},
        related_name='pilgrimage_sponsorship_offers',
        help_text="Level of sponsorship for this pilgrimage"
    )
    sponsor_name = models.CharField(max_length=255, blank=True, null=True, help_text="Name of sponsor if applicable")
    seats_available = models.PositiveIntegerField(default=0)
    per_seat = models.BooleanField(default=True, help_text="Is the price per seat?")
    image = models.URLField(max_length=500, null=True, blank=True, help_text="Main image URL for the offer")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.destination}"

    @property
    def pilgrimage_type_display(self):
        """Returns display string for the pilgrimage type dropdown."""
        if self.pilgrimage_type:
            return self.pilgrimage_type.term
        return None

    @property
    def sponsorship_display(self):
        """Returns display string for the sponsorship dropdown."""
        if self.sponsorship:
            return self.sponsorship.term
        return None

class PilgrimageOfferIncludedItem(models.Model):
    offer = models.ForeignKey(PilgrimageOffer, related_name='included_items', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, help_text="Name of the included item (e.g., Flight, Accommodation, Meals, Guided Tour)")
    description = models.TextField(blank=True, null=True, help_text="Optional description of the included item")

    def __str__(self):
        return f"{self.name} for {self.offer.title}"

    @property
    def offer_display(self):
        if self.offer:
            return {
                "id": self.offer.id,
                "title": self.offer.title,
            }
        return None

class PilgrimageOfferImage(models.Model):
    offer = models.ForeignKey(PilgrimageOffer, related_name='images', on_delete=models.CASCADE)
    image = models.URLField(max_length=500)
    caption = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Image for {self.offer.title}"

    @property
    def offer_display(self):
        if self.offer:
            return {
                "id": self.offer.id,
                "title": self.offer.title,
            }
        return None

# --------- VISA APPLICATION MODEL ---------

def pilgrimage_passport_photo_upload_to(instance, filename):
    return f'pilgrimage_visa/{instance.id or "temp"}/passport_photo/{filename}'

def pilgrimage_medical_certificate_upload_to(instance, filename):
    return f'pilgrimage_visa/{instance.id or "temp"}/medical_certificate/{filename}'

class PilgrimageVisaApplication(models.Model):
    """
    Represents a user's application for a pilgrimage visa offer.
    """
    offer = models.ForeignKey(
        PilgrimageOffer,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name='applications',
        help_text="The pilgrimage offer for which the user is applying."
    )
    applicant = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='pilgrimage_visa_applications'
    )
    passport_number = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    pilgrimage_type = models.ForeignKey(
        TableDropDownDefinition,
        on_delete=models.PROTECT,
        limit_choices_to={'table_name': 'pilgrimage_type', 'is_active': True},
        related_name='pilgrimage_type_applications'
    )
    accommodation_type = models.ForeignKey(
        TableDropDownDefinition,
        on_delete=models.PROTECT,
        limit_choices_to={'table_name': 'pilgrimage_accommodation_type', 'is_active': True},
        related_name='accommodation_type_applications'
    )
    preferred_travel_date = models.DateField()
    group_travel = models.BooleanField(default=False)
    passport_photo = models.FileField(upload_to=pilgrimage_passport_photo_upload_to)
    medical_certificate = models.FileField(upload_to=pilgrimage_medical_certificate_upload_to, blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=255)
    emergency_contact_phone = models.CharField(max_length=30)
    emergency_contact_relationship = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.applicant.get_full_name() or self.applicant.user.username} - {self.offer.title}"

