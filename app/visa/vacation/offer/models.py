from django.db import models
from django_countries.fields import CountryField
from definition.models import TableDropDownDefinition
from account.client.models import Client  # For applicant ForeignKey

from cloudinary.models import CloudinaryField  # Added for Cloudinary file/image fields

class VacationOffer(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    destination = CountryField()
    start_date = models.DateField()
    end_date = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="USD")
    per_seat = models.BooleanField(default=True, help_text="Is the price per seat?")
    hotel_stars = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Hotel star rating if included")
    image = CloudinaryField('image', blank=True, null=True, help_text="Main image for the offer")  # Changed from URLField to CloudinaryField
    # For multiple images, use a related model below
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.destination}"

class VacationOfferIncludedItem(models.Model):
    offer = models.ForeignKey(VacationOffer, related_name='included_items', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, help_text="Name of the included item (e.g., Flight, Hotel, City Tour, Airport Transfer)")
    description = models.TextField(blank=True, null=True, help_text="Optional description of the included item")

    def __str__(self):
        return f"{self.name} for {self.offer.title}"

class VacationOfferImage(models.Model):
    offer = models.ForeignKey(VacationOffer, related_name='images', on_delete=models.CASCADE)
    image = CloudinaryField('image', blank=True, null=True)  # Changed from URLField to CloudinaryField
    caption = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Image for {self.offer.title}"


# ------- VACATION VISA APPLICATION MODEL --------

def vacation_identification_document_upload_to(instance, filename):
    return f'vacation_application/{instance.id or "temp"}/identification_document/{filename}'

class VacationVisaApplication(models.Model):
    """
    Represents a user's application for a vacation offer.
    Only fields unique to the application (not duplicated from the Offer model) are included here.
    Follows the steps:
      1. Personal Information (applicant, passport_number, date_of_birth)
      2. Vacation Details (destination, travel_date, number_of_people, accommodation_type)
      3. Document Uploads (identification_document)
      4. Emergency Contact (emergency_contact_name, emergency_contact_phone, emergency_contact_relationship)
    """
    offer = models.ForeignKey(
        VacationOffer,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name='applications',
        help_text="The vacation offer for which the user is applying."
    )
    applicant = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='vacation_visa_applications'
    )
    passport_number = models.CharField(max_length=50)
    date_of_birth = models.DateField()

    # Vacation Details
    destination = CountryField()
    travel_date = models.DateField()
    number_of_people = models.PositiveIntegerField(default=1, help_text="Number of people in the application")
    accommodation_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Type of accommodation (e.g., Hotel, Apartment, Hostel, None)"
    )

    # Document Uploads
    identification_document = CloudinaryField('file', blank=True, null=True, help_text="Passport, National ID, or other identification document")

    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=255)
    emergency_contact_phone = models.CharField(max_length=30)
    emergency_contact_relationship = models.CharField(max_length=100)

    # Status field: default to "Draft" application status if available
    status = models.ForeignKey(
        TableDropDownDefinition,
        on_delete=models.PROTECT,
        limit_choices_to={'table_name': 'vacation_application_status', 'is_active': True},
        related_name='vacation_visa_applications_status',
        help_text="Status of the vacation visa application",
        null=True,
        blank=True,
        default=None,  # remains None for migrations, default logic enforced in save
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        display_name = None
        try:
            display_name = self.applicant.get_full_name() or self.applicant.user.username
        except Exception:
            display_name = str(self.applicant_id)
        return f"{display_name} - {self.offer.title}"

    @property
    def status_display(self):
        """Returns display string for this application's status dropdown."""
        if self.status:
            return self.status.term
        return None

    def save(self, *args, **kwargs):
        # Make default application status "Draft", if not already set
        if self.status is None:
            try:
                self.status = TableDropDownDefinition.objects.filter(
                    table_name='vacation_application_status',
                    is_active=True,
                    term="Draft"
                ).first()
            except Exception:
                pass
        super().save(*args, **kwargs)
