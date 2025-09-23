from django.db import models

from definition.models import TableDropDownDefinition


class HotelBooking(models.Model):
    destination = models.CharField(max_length=10, help_text="Destination code, e.g., IATA or country code")
    check_in = models.DateField()
    check_out = models.DateField()
    adults = models.PositiveIntegerField(default=1)
    children = models.PositiveIntegerField(default=0)
    rooms = models.PositiveIntegerField(default=1)
    traveling_with_pets = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.ForeignKey(
        TableDropDownDefinition,
        on_delete=models.SET_NULL,
        related_name='hotel_reservation_status',
        limit_choices_to={'table_name': 'hotel_reservation_status'},
        null=True,
        blank=True
    )

    def save(self, *args, **kwargs):
        # Set default status to "Pending" if not already set
        if not self.status:
            try:
                self.status = TableDropDownDefinition.objects.get(
                    table_name='hotel_reservation_status',
                    term__iexact='Pending'
                )
            except TableDropDownDefinition.DoesNotExist:
                pass  # Optionally, handle the case where "Pending" does not exist
        super().save(*args, **kwargs)

    def __str__(self):
        return f"HotelBooking to {self.destination} from {self.check_in} to {self.check_out} ({self.adults} adults, {self.children} children, {self.rooms} rooms)"


class Amenity(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Name of the amenity, e.g., Free WiFi, Pool")
    image = models.URLField(max_length=500, blank=True, null=True, help_text="Optional icon URL for the amenity")

    def __str__(self):
        return self.name

class Hotel(models.Model):
    image = models.URLField(max_length=500, help_text="URL to the hotel's avatar image")
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=500, help_text="Full address of the hotel")
    city = models.CharField(max_length=100, help_text="City where the hotel is located")
    country = models.CharField(max_length=100, help_text="Country where the hotel is located")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Latitude of the hotel")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Longitude of the hotel")
    rating = models.DecimalField(max_digits=3, decimal_places=2, help_text="Hotel rating, e.g., 4.5")
    reviews = models.TextField(blank=True, null=True, help_text="Optional reviews or review summary")
    price = models.CharField(max_length=100, help_text="Price or price range as a string")
    description = models.TextField()
    amenities = models.ManyToManyField(Amenity, blank=True, related_name="hotels", help_text="Available amenities in this hotel")
    phone_number = models.CharField(max_length=50, blank=True, null=True, help_text="Contact phone number for the hotel")
    email = models.EmailField(blank=True, null=True, help_text="Contact email for the hotel")
    website = models.URLField(max_length=500, blank=True, null=True, help_text="Hotel's website URL")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.rating})"


