from django.urls import path
from .flight.views import search_flights

urlpatterns = [
    path("search-flights/", search_flights, name="search_flights"),
]
