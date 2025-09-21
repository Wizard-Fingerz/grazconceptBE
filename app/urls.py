from django.urls import path
from .flight.views import get_booked_flights, search_flights, suggest_flights_for_user, suggest_locations

urlpatterns = [
    path("search-flights/", search_flights, name="search_flights"),
    path("booked-flights/", get_booked_flights, name="get_booked_flights"),
    path("suggest-flights/", suggest_flights_for_user, name="suggest_flights_for_user"),
    path("suggest-locations/", suggest_locations, name="suggest_locations"),
]
