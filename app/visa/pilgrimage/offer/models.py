from django.db import models
from django_countries.fields import CountryField
from definition.models import TableDropDownDefinition

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
    image = models.ImageField(upload_to='pilgrimage_offers/main/', null=True, blank=True, help_text="Main image for the offer")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.destination}"

    @property
    def pilgrimage_type_display(self):
        """Returns a dictionary with id and term for the pilgrimage type dropdown."""
        if self.pilgrimage_type:
            return self.pilgrimage_type.term,
        return None

    @property
    def sponsorship_display(self):
        """Returns a dictionary with id and term for the sponsorship dropdown."""
        if self.sponsorship:
            return  self.sponsorship.term,
            
        return None

class PilgrimageOfferIncludedItem(models.Model):
    offer = models.ForeignKey(PilgrimageOffer, related_name='included_items', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, help_text="Name of the included item (e.g., Flight, Accommodation, Meals, Guided Tour)")
    description = models.TextField(blank=True, null=True, help_text="Optional description of the included item")

    def __str__(self):
        return f"{self.name} for {self.offer.title}"

    @property
    def offer_display(self):
        """Returns a simple dict for the related offer."""
        if self.offer:
            return {
                "id": self.offer.id,
                "title": self.offer.title,
            }
        return None

class PilgrimageOfferImage(models.Model):
    offer = models.ForeignKey(PilgrimageOffer, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='pilgrimage_offers/gallery/')
    caption = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Image for {self.offer.title}"

    @property
    def offer_display(self):
        """Returns a simple dict for the related offer."""
        if self.offer:
            return {
                "id": self.offer.id,
                "title": self.offer.title,
            }
        return None
