from django.urls import path, include
from rest_framework.routers import DefaultRouter

from app.ad_banners.views import AdBannerViewSet
from app.visa.study.views import StudyVisaApplicationViewSet
from .flight.views import get_booked_flights, search_flights, suggest_flights_for_user, suggest_locations
from .hotels.views import HotelBookingViewSet, HotelViewSet
from .visa.study.institutions.views import (
    CountryViewSet,
    CityViewSet,
    ProgramTypeViewSet,
    InstitutionViewSet,
    CourseOfStudyViewSet,
)

router = DefaultRouter()
router.register(r'hotel-bookings', HotelBookingViewSet, basename='hotelbooking')
router.register(r'hotels', HotelViewSet, basename='hotels')
router.register(r'countries', CountryViewSet, basename='countries')
router.register(r'cities', CityViewSet, basename='cities')
router.register(r'program-types', ProgramTypeViewSet, basename='programtypes')
router.register(r'institutions', InstitutionViewSet, basename='institutions')
router.register(r'courses-of-study', CourseOfStudyViewSet, basename='coursesofstudy')
router.register(r'study-visa-application', StudyVisaApplicationViewSet, basename='studyvisaapplication')
router.register(r'ad-banner', AdBannerViewSet, basename='adbanner')

urlpatterns = [
    path("search-flights/", search_flights, name="search_flights"),
    path("booked-flights/", get_booked_flights, name="get_booked_flights"),
    path("suggest-flights/", suggest_flights_for_user, name="suggest_flights_for_user"),
    path("suggest-locations/", suggest_locations, name="suggest_locations"),
    path("", include(router.urls)),
]
