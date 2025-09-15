import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .models import FlightBooking

AVIATIONSTACK_BASE_URL = "https://api.aviationstack.com/v1/flightsFuture"



@api_view(["POST"])
def search_flights(request):
    """
    Handle flight booking search and persist booking.
    """
    data = request.data
    flight_type = data.get("flightType")

    # Basic validation
    if flight_type not in ["Round Trip", "One Way", "Multi-city"]:
        return Response({"error": "Invalid flight type"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        flights_found = []

        if flight_type in ["Round Trip", "One Way"]:
            params = {
                "access_key": settings.AVIATIONSTACK_API_KEY,
                "dep_iata": data.get("from"),
                "arr_iata": data.get("to"),
                "date": data.get("departureDate"),
            }
            res = requests.get(AVIATIONSTACK_BASE_URL, params=params)
            flights_found.append(res.json())

            if flight_type == "Round Trip" and data.get("returnDate"):
                return_params = {
                    "access_key": settings.AVIATIONSTACK_API_KEY,
                    "dep_iata": data.get("to"),
                    "arr_iata": data.get("from"),
                    "date": data.get("returnDate"),
                }
                res_return = requests.get(AVIATIONSTACK_BASE_URL, params=return_params)
                flights_found.append(res_return.json())

        elif flight_type == "Multi-city":
            for seg in data.get("multiCitySegments", []):
                params = {
                    "access_key": settings.AVIATIONSTACK_API_KEY,
                    "dep_iata": seg.get("from"),
                    "arr_iata": seg.get("to"),
                    "date": seg.get("departureDate"),
                }
                res = requests.get(AVIATIONSTACK_BASE_URL, params=params)
                flights_found.append(res.json())

        # Save booking record
        booking = FlightBooking.objects.create(
            flight_type=flight_type,
            from_airport=data.get("from"),
            to_airport=data.get("to"),
            departure_date=data.get("departureDate") or None,
            return_date=data.get("returnDate") or None,
            multi_city_segments=data.get("multiCitySegments", []),
            adults=data.get("adults", 1),
            children=data.get("children", 0),
            infants=data.get("infants", 0),
            students=data.get("students", 0),
            seniors=data.get("seniors", 0),
            youths=data.get("youths", 0),
            toddlers=data.get("toddlers", 0),
            cabin_class=data.get("cabinClass", "Economy"),
            flights_found=flights_found,  # store API response
        )

        return Response({
            "message": "Flights retrieved and booking created successfully",
            "booking_id": booking.id,
            "flights_found": flights_found,
        }, status=status.HTTP_201_CREATED)

    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
