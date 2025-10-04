from django.db import models
from account.client.models import Client

class FlightBooking(models.Model):
    FLIGHT_TYPES = [
        ("One Way", "One Way"),
        ("Round Trip", "Round Trip"),
        ("Multi-city", "Multi-city"),
    ]
    client = models.ForeignKey('account.Client', on_delete = models.CASCADE)
    flight_type = models.CharField(max_length=250, choices=FLIGHT_TYPES)
    from_airport = models.CharField(max_length=250, blank=True, null=True)
    to_airport = models.CharField(max_length=250, blank=True, null=True)
    departure_date = models.DateField(blank=True, null=True)
    return_date = models.DateField(blank=True, null=True)

    # Multi-city stored as JSON
    multi_city_segments = models.JSONField(blank=True, null=True)

    # Travelers
    adults = models.IntegerField(default=1)
    children = models.IntegerField(default=0)
    infants = models.IntegerField(default=0)
    students = models.IntegerField(default=0)
    seniors = models.IntegerField(default=0)
    youths = models.IntegerField(default=0)
    toddlers = models.IntegerField(default=0)

    cabin_class = models.CharField(max_length=20, default="Economy")

    # Flight search response (for reference / debugging)
    flights_found = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.flight_type} booking from {self.from_airport} to {self.to_airport}"
