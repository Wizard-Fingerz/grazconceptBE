import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .models import FlightBooking

AMADEUS_BASE_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"
AMADEUS_AUTH_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"

def get_amadeus_access_token():
    """
    Obtain an access token from Amadeus API using client credentials.
    """
    payload = {
        "grant_type": "client_credentials",
        "client_id": settings.AMADEUS_CLIENT_ID,
        "client_secret": settings.AMADEUS_CLIENT_SECRET,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(AMADEUS_AUTH_URL, data=payload, headers=headers)
    response.raise_for_status()
    return response.json()["access_token"]

def build_amadeus_search_params(data, segment=None):
    """
    Build Amadeus API search parameters from request data.
    If segment is provided, use it for multi-city.
    """
    if segment:
        origin = segment.get("from")
        destination = segment.get("to")
        departure_date = segment.get("departureDate")
    else:
        origin = data.get("from")
        destination = data.get("to")
        departure_date = data.get("departureDate")

    params = {
        "originLocationCode": origin,
        "destinationLocationCode": destination,
        "departureDate": departure_date,
        "adults": data.get("adults", 1),
        "children": data.get("children", 0),
        "infants": data.get("infants", 0),
        "travelClass": data.get("cabinClass", "ECONOMY").upper(),
        "nonStop": False,
        "currencyCode": data.get("currencyCode", "USD"),
        "max": 10,
    }
    # Remove zero passengers to avoid Amadeus API errors
    params = {k: v for k, v in params.items() if not (isinstance(v, int) and v == 0)}
    return params

@api_view(["POST"])
def search_flights(request):
    """
    Handle flight booking search and persist booking.
    The request user is set as the client for the booking.
    """
    data = request.data
    flight_type = data.get("flightType")

    # Basic validation
    if flight_type not in ["Round Trip", "One Way", "Multi-city"]:
        return Response({"error": "Invalid flight type"}, status=status.HTTP_400_BAD_REQUEST)

    # Ensure the user is authenticated
    user = request.user
    if not user.is_authenticated:
        return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

    # Check if user is actually a Client instance (since Client extends User via multi-table inheritance)
    print(user)
    from account.client.models import Client
    try:
        # Try to get the related Client instance for this user
        client = Client.objects.get(email=user)
    except Client.DoesNotExist:
        return Response({"error": "User is not a client"}, status=status.HTTP_403_FORBIDDEN)
    except AttributeError:
        return Response({"error": "User is not a client"}, status=status.HTTP_403_FORBIDDEN)

    try:
        access_token = get_amadeus_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}
        flights_found = []

        if flight_type in ["Round Trip", "One Way"]:
            params = build_amadeus_search_params(data)
            if flight_type == "Round Trip" and data.get("returnDate"):
                # Amadeus supports round trip in one call using "returnDate"
                params["returnDate"] = data.get("returnDate")
            response = requests.get(AMADEUS_BASE_URL, params=params, headers=headers)
            response.raise_for_status()
            flights_found.append(response.json())

        elif flight_type == "Multi-city":
            # Amadeus supports multi-city via "itineraries" in POST, but for simplicity, do multiple GETs
            for seg in data.get("multiCitySegments", []):
                params = build_amadeus_search_params(data, segment=seg)
                response = requests.get(AMADEUS_BASE_URL, params=params, headers=headers)
                response.raise_for_status()
                flights_found.append(response.json())

        # Save booking record with the request user as client
        booking = FlightBooking.objects.create(
            client=client,
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
