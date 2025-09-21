from django.db import models





class HotelBooking(models.Model):
    destination = models.CharField(max_length=10, help_text="Destination code, e.g., IATA or country code")
    check_in = models.DateField()
    check_out = models.DateField()
    adults = models.PositiveIntegerField(default=1)
    children = models.PositiveIntegerField(default=0)
    rooms = models.PositiveIntegerField(default=1)
    traveling_with_pets = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"HotelBooking to {self.destination} from {self.check_in} to {self.check_out} ({self.adults} adults, {self.children} children, {self.rooms} rooms)"
