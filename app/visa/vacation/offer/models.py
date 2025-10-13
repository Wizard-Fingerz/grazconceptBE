from django.db import models
from django_countries.fields import CountryField

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
    image = models.URLField(max_length=500, null=True, blank=True, help_text="Main image URL for the offer")
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
    image = models.URLField(max_length=500)
    caption = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Image for {self.offer.title}"
