from django.db import models
from django_countries.fields import CountryField
from definition.models import TableDropDownDefinition
from account.client.models import Client  # For applicant ForeignKey
from django.conf import settings

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

def application_comment_attachment_upload_to(instance, filename):
    # Each comment's attachments go into their own directory keyed by visa app and comment id (or temp)
    comment_id = instance.id or "temp"
    visa_app_id = instance.visa_application.id if instance.visa_application_id else "temp"
    return f'pilgrimage_visa/{visa_app_id}/comments/{comment_id}/{filename}'

class PilgrimageVisaApplication(models.Model):
    """
    Represents a user's application for a pilgrimage visa offer.
    Only fields unique to the application (not duplicated from the Offer model) are included here.
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
    preferred_travel_date = models.DateField()
    group_travel = models.BooleanField(default=False)
    passport_photo = models.FileField(upload_to=pilgrimage_passport_photo_upload_to)
    medical_certificate = models.FileField(upload_to=pilgrimage_medical_certificate_upload_to, blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=255)
    emergency_contact_phone = models.CharField(max_length=30)
    emergency_contact_relationship = models.CharField(max_length=100)
    # Status field: default to "Draft" application status if available
    status = models.ForeignKey(
        TableDropDownDefinition,
        on_delete=models.PROTECT,
        limit_choices_to={'table_name': 'pilgrimage_application_status', 'is_active': True},
        related_name='pilgrimage_visa_applications_status',
        help_text="Status of the pilgrimage visa application",
        null=True,
        blank=True,
        default=None,  # this remains None for migrations, default logic enforced in save
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        # Use Client's true name if available via properties or fallback, for better client name display
        name = None
        if self.applicant:
            # Display using Client's username, or if possible, use user.get_full_name, plus fallback to first/last or email
            user = getattr(self.applicant, "user", None)
            # 1. Try get_full_name
            if user and hasattr(user, "get_full_name") and callable(user.get_full_name):
                name = user.get_full_name()
            # 2. Try user.username
            if (not name or not name.strip()) and user and hasattr(user, "username"):
                name = getattr(user, "username", None)
            # 3. Try applicant.username (since Client inherits User)
            if (not name or not name.strip()):
                name = getattr(self.applicant, "username", None)
            # 4. Try first and last name
            if (not name or not name.strip()):
                if user:
                    first_name = getattr(user, "first_name", "") or ""
                    last_name = getattr(user, "last_name", "") or ""
                    joined = f"{first_name} {last_name}".strip()
                    if joined:
                        name = joined
            # 5. If all else fails, fallback to email
            if (not name or not name.strip()):
                if user and hasattr(user, "email") and user.email:
                    name = user.email
            # 6. As last resort, just say Applicant ID
            if (not name or not name.strip()):
                name = f"Applicant ID {self.applicant.id}"

        if not name:
            name = ""
        return f"{name} - {self.offer.title}"

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
                    table_name='pilgrimage_application_status',
                    is_active=True,
                    term="Draft"
                ).first()
            except Exception:
                pass
        super().save(*args, **kwargs)

class PilgrimageVisaApplicationComment(models.Model):
    """
    A comment/feedback on a PilgrimageVisaApplication, for communication between admin/agent and applicant.
    """
    visa_application = models.ForeignKey(
        PilgrimageVisaApplication,
        related_name='comments',
        on_delete=models.CASCADE,
        help_text="The pilgrimage visa application this comment belongs to."
    )
    # Either an agent/admin user or the applicant can post (applicant easiest as a Client FK, admin as User)
    applicant = models.ForeignKey(
        Client,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='application_comments_sent',
        help_text="Set if this comment is from the applicant."
    )
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='visa_application_comments_admin',
        help_text="Set if this comment is from an admin/agent user."
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read_by_applicant = models.BooleanField(default=False)
    is_read_by_admin = models.BooleanField(default=False)
    # (optional) Document upload to clarify/request something
    attachment = models.FileField(
        upload_to=application_comment_attachment_upload_to,
        null=True, blank=True,
        help_text="Optional file/document related to this comment."
    )

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        sender = None
        if self.applicant:
            # Prefer displaying the true client name, as in the PilgrimageVisaApplication above
            user = getattr(self.applicant, "user", None)
            name = None
            if user and hasattr(user, "get_full_name") and callable(user.get_full_name):
                name = user.get_full_name()
            if (not name or not name.strip()) and user and hasattr(user, "username"):
                name = getattr(user, "username", None)
            if (not name or not name.strip()):
                name = getattr(self.applicant, "username", None)
            if (not name or not name.strip()):
                if user:
                    first_name = getattr(user, "first_name", "") or ""
                    last_name = getattr(user, "last_name", "") or ""
                    joined = f"{first_name} {last_name}".strip()
                    if joined:
                        name = joined
            if (not name or not name.strip()):
                if user and hasattr(user, "email") and user.email:
                    name = user.email
            if (not name or not name.strip()):
                name = f"Applicant ID {self.applicant.id}"
            sender = f"Applicant: {name}"
        elif self.admin:
            # Defensive: Admin might not have get_full_name
            if hasattr(self.admin, "get_full_name") and callable(self.admin.get_full_name):
                name = self.admin.get_full_name()
                if not name:
                    name = getattr(self.admin, "username", None)
            else:
                name = getattr(self.admin, "username", None)
            if not name:
                name = f"Admin ID {self.admin.id}"
            sender = f"Admin: {name}"
        else:
            sender = "Unknown"
        return f"Comment by {sender} on application {self.visa_application.id}"

    @property
    def sender_type(self):
        if self.applicant and self.admin:
            return "applicant+admin"
        elif self.applicant:
            return "applicant"
        elif self.admin:
            return "admin"
        return "unknown"

    @property
    def sender_display(self):
        # For serializers/UI, show info about who sent the comment, always safe.
        if self.applicant:
            user = getattr(self.applicant, "user", None)
            name = None
            if user and hasattr(user, "get_full_name") and callable(user.get_full_name):
                name = user.get_full_name()
            if (not name or not name.strip()) and user and hasattr(user, "username"):
                name = getattr(user, "username", None)
            if (not name or not name.strip()):
                name = getattr(self.applicant, "username", None)
            if (not name or not name.strip()):
                if user:
                    first_name = getattr(user, "first_name", "") or ""
                    last_name = getattr(user, "last_name", "") or ""
                    joined = f"{first_name} {last_name}".strip()
                    if joined:
                        name = joined
            if (not name or not name.strip()):
                if user and hasattr(user, "email") and user.email:
                    name = user.email
            if (not name or not name.strip()):
                name = f"Applicant ID {self.applicant.id}"
            return {
                "type": "applicant",
                "name": name,
                "id": self.applicant.id,
            }
        elif self.admin:
            if hasattr(self.admin, "get_full_name") and callable(self.admin.get_full_name):
                name = self.admin.get_full_name()
                if not name:
                    name = getattr(self.admin, "username", None)
            else:
                name = getattr(self.admin, "username", None)
            if not name:
                name = f"Admin ID {self.admin.id}"
            return {
                "type": "admin",
                "name": name,
                "id": self.admin.id,
            }
        return {"type": "unknown"}

