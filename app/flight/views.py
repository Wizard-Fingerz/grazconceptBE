import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .models import FlightBooking

AMADEUS_BASE_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"
AMADEUS_AUTH_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
AMADEUS_LOCATION_URL = "https://test.api.amadeus.com/v1/reference-data/locations"

def get_amadeus_access_token():
    payload = {
        "grant_type": "client_credentials",
        "client_id": settings.AMADEUS_CLIENT_ID,
        "client_secret": settings.AMADEUS_CLIENT_SECRET,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(AMADEUS_AUTH_URL, data=payload, headers=headers)
    response.raise_for_status()
    return response.json()["access_token"]

def search_locations(keyword, access_token, country_code=None, limit=10, offset=0, sort="analytics.travelers.score", view="FULL", sub_type="AIRPORT,CITY"):
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "keyword": keyword,
        "subType": sub_type,
        "page[limit]": limit,
        "page[offset]": offset,
        "sort": sort,
        "view": view,
    }
    if country_code:
        params["countryCode"] = country_code
    response = requests.get(AMADEUS_LOCATION_URL, params=params, headers=headers)
    response.raise_for_status()
    return response.json().get("data", [])

def get_iata_code_from_location_search(location, access_token, country_code=None):
    if not location or not isinstance(location, str):
        return None
    location = location.strip().upper()
    if len(location) == 3 and location.isalpha():
        return location
    try:
        locations = search_locations(location, access_token, country_code=country_code, limit=1)
        if locations and "iataCode" in locations[0]:
            return locations[0]["iataCode"]
    except Exception:
        pass
    return None

def build_amadeus_search_params(data, access_token, segment=None, origin_code=None, destination_code=None):
    if segment:
        origin = segment.get("from")
        destination = segment.get("to")
        departure_date = segment.get("departureDate")
        origin_country = segment.get("fromCountryCode")
        destination_country = segment.get("toCountryCode")
    else:
        origin = data.get("from")
        destination = data.get("to")
        departure_date = data.get("departureDate")
        origin_country = data.get("fromCountryCode")
        destination_country = data.get("toCountryCode")

    if not origin_code:
        origin_code = get_iata_code_from_location_search(origin, access_token, country_code=origin_country)
    if not destination_code:
        destination_code = get_iata_code_from_location_search(destination, access_token, country_code=destination_country)

    def is_iata_code(val):
        return isinstance(val, str) and len(val) == 3 and val.isalpha()

    if not is_iata_code(origin_code):
        return {"error": f"originLocationCode must be a valid 3-letter IATA code (e.g. 'BOS'). Could not resolve '{origin}'."}
    if not is_iata_code(destination_code):
        return {"error": f"destinationLocationCode must be a valid 3-letter IATA code (e.g. 'PAR'). Could not resolve '{destination}'."}

    params = {
        "originLocationCode": origin_code,
        "destinationLocationCode": destination_code,
        "departureDate": departure_date,
        "adults": data.get("adults", 1),
        "children": data.get("children", 0),
        "infants": data.get("infants", 0),
        "travelClass": data.get("cabinClass", "ECONOMY").upper(),
        "nonStop": data.get("nonStop", False),
        "currencyCode": data.get("currencyCode", "USD"),
        "max": min(int(data.get("max", 10)), 250),
    }
    if data.get("includedAirlineCodes"):
        params["includedAirlineCodes"] = data.get("includedAirlineCodes")
    if data.get("excludedAirlineCodes"):
        params["excludedAirlineCodes"] = data.get("excludedAirlineCodes")
    if data.get("maxPrice"):
        try:
            max_price = int(data.get("maxPrice"))
            if max_price > 0:
                params["maxPrice"] = max_price
        except Exception:
            pass
    params = {k: v for k, v in params.items() if not (isinstance(v, int) and v == 0)}
    return params

@api_view(["POST"])
def search_flights(request):
    """
    Enhanced: For a given country or city, map all airports/cities and search for flights between all possible pairs.
    This increases the chance of finding flights even if the main city/airport has no direct flights.
    """
    data = request.data
    flight_type = data.get("flightType")

    if flight_type not in ["Round Trip", "One Way", "Multi-city"]:
        return Response({"error": "Invalid flight type"}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    if not user.is_authenticated:
        return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

    from account.client.models import Client
    try:
        client = Client.objects.get(email=user)
    except Client.DoesNotExist:
        return Response({"error": "User is not a client"}, status=status.HTTP_403_FORBIDDEN)
    except AttributeError:
        return Response({"error": "User is not a client"}, status=status.HTTP_403_FORBIDDEN)

    try:
        access_token = get_amadeus_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}
        flights_found = []
        location_search_results = {}

        if flight_type in ["Round Trip", "One Way"]:
            from_location = data.get("from")
            to_location = data.get("to")
            from_country = data.get("fromCountryCode")
            to_country = data.get("toCountryCode")

            origin_locations = search_locations(from_location, access_token, country_code=from_country, limit=10)
            destination_locations = search_locations(to_location, access_token, country_code=to_country, limit=10)

            location_search_results["origin"] = origin_locations
            location_search_results["destination"] = destination_locations

            if not origin_locations or not destination_locations:
                return Response({
                    "error": "Could not find valid airports or cities for the provided locations.",
                    "origin_search_results": origin_locations,
                    "destination_search_results": destination_locations
                }, status=status.HTTP_400_BAD_REQUEST)

            flight_searches = []
            for origin in origin_locations:
                for destination in destination_locations:
                    origin_code = origin.get("iataCode")
                    destination_code = destination.get("iataCode")
                    if not origin_code or not destination_code:
                        continue
                    params = build_amadeus_search_params(data, access_token, origin_code=origin_code, destination_code=destination_code)
                    if isinstance(params, dict) and "error" in params:
                        continue
                    if flight_type == "Round Trip" and data.get("returnDate"):
                        params["returnDate"] = data.get("returnDate")
                    try:
                        response = requests.get(AMADEUS_BASE_URL, params=params, headers=headers)
                        if response.status_code == 200:
                            result = response.json()
                            if result.get("data"):
                                flights_found.append({
                                    "origin": origin,
                                    "destination": destination,
                                    "flights": result.get("data")
                                })
                        elif response.status_code == 400:
                            continue
                        else:
                            response.raise_for_status()
                    except Exception:
                        continue

            if not flights_found:
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
                    flights_found=flights_found,
                )
                return Response({
                    "message": "No flights found between any mapped locations.",
                    "booking_id": booking.id,
                    "flights_found": [],
                    "origin_search_results": origin_locations,
                    "destination_search_results": destination_locations
                }, status=status.HTTP_200_OK)

        elif flight_type == "Multi-city":
            multi_city_segments = data.get("multiCitySegments", [])
            location_search_results["multiCitySegments"] = []
            for seg in multi_city_segments:
                from_location = seg.get("from")
                to_location = seg.get("to")
                from_country = seg.get("fromCountryCode")
                to_country = seg.get("toCountryCode")

                origin_locations = search_locations(from_location, access_token, country_code=from_country, limit=10)
                destination_locations = search_locations(to_location, access_token, country_code=to_country, limit=10)

                location_search_results["multiCitySegments"].append({
                    "origin": origin_locations,
                    "destination": destination_locations
                })

                if not origin_locations or not destination_locations:
                    return Response({
                        "error": "Could not find valid airports or cities for one of the multi-city segments.",
                        "segment": seg,
                        "origin_search_results": origin_locations,
                        "destination_search_results": destination_locations
                    }, status=status.HTTP_400_BAD_REQUEST)

                segment_flights = []
                for origin in origin_locations:
                    for destination in destination_locations:
                        origin_code = origin.get("iataCode")
                        destination_code = destination.get("iataCode")
                        if not origin_code or not destination_code:
                            continue
                        params = build_amadeus_search_params(data, access_token, segment=seg, origin_code=origin_code, destination_code=destination_code)
                        if isinstance(params, dict) and "error" in params:
                            continue
                        try:
                            response = requests.get(AMADEUS_BASE_URL, params=params, headers=headers)
                            if response.status_code == 200:
                                result = response.json()
                                if result.get("data"):
                                    segment_flights.append({
                                        "origin": origin,
                                        "destination": destination,
                                        "flights": result.get("data")
                                    })
                            elif response.status_code == 400:
                                continue
                            else:
                                response.raise_for_status()
                        except Exception:
                            continue
                if segment_flights:
                    flights_found.append(segment_flights)

            if not flights_found:
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
                    flights_found=flights_found,
                )
                return Response({
                    "message": "No flights found for any multi-city segment between mapped locations.",
                    "booking_id": booking.id,
                    "flights_found": [],
                    "multiCitySegments_search_results": location_search_results["multiCitySegments"]
                }, status=status.HTTP_200_OK)

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
            flights_found=flights_found,
        )

        return Response({
            "message": "Flights retrieved and booking created successfully",
            "booking_id": booking.id,
            "flights_found": flights_found,
            "location_search_results": location_search_results
        }, status=status.HTTP_201_CREATED)

    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except ValueError as ve:
        return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
def get_booked_flights(request):
    """
    Returns all available flights (FlightBooking records) for the authenticated user.
    """
    user = request.user
    if not user.is_authenticated:
        return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

    from account.client.models import Client
    try:
        client = Client.objects.get(email=user)
    except Client.DoesNotExist:
        return Response({"error": "User is not a client"}, status=status.HTTP_403_FORBIDDEN)
    except AttributeError:
        return Response({"error": "User is not a client"}, status=status.HTTP_403_FORBIDDEN)

    bookings = FlightBooking.objects.filter(client=client).order_by('-created_at')
    results = []
    for booking in bookings:
        results.append({
            "id": booking.id,
            "flight_type": booking.flight_type,
            "from_airport": booking.from_airport,
            "to_airport": booking.to_airport,
            "departure_date": booking.departure_date,
            "return_date": booking.return_date,
            "multi_city_segments": booking.multi_city_segments,
            "adults": booking.adults,
            "children": booking.children,
            "infants": booking.infants,
            "students": booking.students,
            "seniors": booking.seniors,
            "youths": booking.youths,
            "toddlers": booking.toddlers,
            "cabin_class": booking.cabin_class,
            "flights_found": booking.flights_found,
            "created_at": booking.created_at,
        })
    return Response({"available_flights": results}, status=status.HTTP_200_OK)

@api_view(["GET"])
def suggest_flights_for_user(request):
    """
    Returns a random set of available flights from Amadeus, ignoring user location and previous bookings.
    This is a fallback for when location-based suggestions are not working.
    The departure date is set to today.
    """
    import datetime

    user = request.user
    if not user.is_authenticated:
        return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

    from account.client.models import Client
    try:
        client = Client.objects.get(email=user)
    except Exception:
        return Response({"error": "User is not a client"}, status=status.HTTP_403_FORBIDDEN)

    today = datetime.date.today()
    departure_date = today.isoformat()

    adults = int(request.query_params.get("adults", 1))
    children = int(request.query_params.get("children", 0))
    infants = int(request.query_params.get("infants", 0))
    cabin_class = request.query_params.get("cabinClass", "ECONOMY")
    non_stop = request.query_params.get("nonStop", "false").lower() == "true"
    currency_code = request.query_params.get("currencyCode", "USD")
    max_results = int(request.query_params.get("max", 10))

    major_airports = [
        "JFK", "LHR", "CDG", "DXB", "HND", "LAX", "ORD", "ATL", "FRA", "AMS",
        "SIN", "ICN", "DFW", "DEN", "MAD", "BCN", "YYZ", "SYD", "GRU", "MEX"
    ]

    import random
    origin_code = random.choice(major_airports)
    destination_code = random.choice([code for code in major_airports if code != origin_code])

    search_data = {
        "from": origin_code,
        "to": destination_code,
        "departureDate": departure_date,
        "adults": adults,
        "children": children,
        "infants": infants,
        "cabinClass": cabin_class,
        "nonStop": non_stop,
        "currencyCode": currency_code,
        "max": max_results,
    }

    try:
        access_token = get_amadeus_access_token()
    except Exception as e:
        return Response({"error": f"Failed to get Amadeus access token: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    params = build_amadeus_search_params(search_data, access_token)
    if "error" in params:
        return Response({"error": params["error"]}, status=status.HTTP_400_BAD_REQUEST)

    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    try:
        response = requests.get(AMADEUS_BASE_URL, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        flights = data.get("data", [])
        if not flights:
            return Response({
                "error": "No random flights found at this time.",
                "origin": origin_code,
                "destination": destination_code
            }, status=status.HTTP_404_NOT_FOUND)
        return Response({
            "origin": origin_code,
            "destination": destination_code,
            "departure_date": departure_date,
            "flights": flights
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            "error": f"Failed to fetch random flights: {str(e)}",
            "origin": origin_code,
            "destination": destination_code
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET"])
def suggest_locations(request):
    """
    Suggest all airports and cities in the user's country if no query is provided,
    or filter by query and/or countryCode if provided.
    Query params:
        - q: partial location string (optional)
        - countryCode: optional, restrict to a country (if not provided, use user's current location)
        - limit: optional, number of results (default 10)
    """
    query = request.GET.get("q")
    country_code = request.GET.get("countryCode")
    limit = int(request.GET.get("limit", 10))

    # If country_code is not provided, try to infer from user's current location (IP-based)
    if not country_code:
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
        if ip_address:
            ip_address = ip_address.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        try:
            if ip_address and ip_address != "127.0.0.1":
                geo_resp = requests.get(f"https://ipapi.co/{ip_address}/json/")
                if geo_resp.status_code == 200:
                    geo_data = geo_resp.json()
                    country_code = geo_data.get("country_code")
        except Exception:
            country_code = None

    # If neither query nor country_code is provided, cannot suggest anything meaningful
    if (not query or not query.strip()) and not country_code:
        return Response(
            {
                "error": "Query parameter 'q' is required if countryCode cannot be determined from your location. "
                         "There is no way to suggest locations without either a search query or knowing where you are browsing from at this point in time."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        access_token = get_amadeus_access_token()
        suggestions = []
        used_query = None

        # If query is not provided, show all airports and cities in the user's country
        if not query or not query.strip():
            # Amadeus API requires a keyword, so we use a loop of all alphanumeric characters to maximize coverage
            # and aggregate results, deduplicating by IATA code.
            import string
            seen_iata = set()
            # Try all letters and digits as starting keyword
            for ch in string.ascii_uppercase + string.digits:
                locations = search_locations(
                    ch,
                    access_token,
                    country_code=country_code,
                    limit=50,  # Use a higher limit to get more results per call
                    sub_type="AIRPORT,CITY"
                )
                for loc in locations:
                    iata_code = loc.get("iataCode")
                    if iata_code and isinstance(iata_code, str) and len(iata_code) == 3 and iata_code not in seen_iata:
                        suggestions.append({
                            "iataCode": iata_code,
                            "name": loc.get("name"),
                            "subType": loc.get("subType"),
                            "countryCode": loc.get("address", {}).get("countryCode"),
                            "cityName": loc.get("address", {}).get("cityName"),
                        })
                        seen_iata.add(iata_code)
                # Stop if we have enough suggestions
                if len(suggestions) >= limit:
                    break
            # Truncate to limit
            suggestions = suggestions[:limit]
            used_query = "ALL"
        else:
            # If query is provided, just use it
            locations = search_locations(
                query.strip(),
                access_token,
                country_code=country_code,
                limit=limit,
                sub_type="AIRPORT,CITY"
            )
            seen_iata = set()
            for loc in locations:
                iata_code = loc.get("iataCode")
                if iata_code and isinstance(iata_code, str) and len(iata_code) == 3 and iata_code not in seen_iata:
                    suggestions.append({
                        "iataCode": iata_code,
                        "name": loc.get("name"),
                        "subType": loc.get("subType"),
                        "countryCode": loc.get("address", {}).get("countryCode"),
                        "cityName": loc.get("address", {}).get("cityName"),
                    })
                    seen_iata.add(iata_code)
            used_query = query.strip()

        if not suggestions:
            return Response({
                "suggestions": [],
                "used_country_code": country_code,
                "used_query": used_query,
                "message": (
                    "No locations found. This may be because there are no airports/cities matching your query "
                    "or country. If you are searching by country, try using a valid IATA code (e.g. 'LOS' for Lagos, Nigeria) "
                    "or a more specific city/airport name."
                )
            }, status=status.HTTP_200_OK)
        return Response({
            "suggestions": suggestions,
            "used_country_code": country_code,
            "used_query": used_query
        }, status=status.HTTP_200_OK)
    except requests.HTTPError as e:
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
            except Exception:
                error_detail = e.response.text
            return Response({
                "error": f"Amadeus API error: {e.response.status_code} {e.response.reason}",
                "detail": error_detail
            }, status=e.response.status_code)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
