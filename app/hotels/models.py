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
