from django.contrib import admin

# Register your models here.
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from app.ad_banners.models import AdBanner

from .hotels.models import Hotel, HotelBooking, Amenity
from .flight.models import FlightBooking
from .visa.study.institutions.models import ProgramType, Institution, CourseOfStudy
from .visa.study.offers.models import StudyVisaOffer, StudyVisaOfferRequirement


class HotelResource(resources.ModelResource):
    class Meta:
        model = Hotel

class HotelBookingResource(resources.ModelResource):
    class Meta:
        model = HotelBooking

class AmenityResource(resources.ModelResource):
    class Meta:
        model = Amenity

class FlightBookingResource(resources.ModelResource):
    class Meta:
        model = FlightBooking

class StudyVisaOfferResource(resources.ModelResource):
    class Meta:
        model = StudyVisaOffer

class StudyVisaOfferRequirementResource(resources.ModelResource):
    class Meta:
        model = StudyVisaOfferRequirement

@admin.register(Hotel)
class HotelAdmin(ImportExportModelAdmin):
    resource_class = HotelResource

@admin.register(HotelBooking)
class HotelBookingAdmin(ImportExportModelAdmin):
    resource_class = HotelBookingResource

@admin.register(Amenity)
class AmenityAdmin(ImportExportModelAdmin):
    resource_class = AmenityResource

@admin.register(FlightBooking)
class FlightBookingAdmin(ImportExportModelAdmin):
    resource_class = FlightBookingResource

@admin.register(StudyVisaOffer)
class StudyVisaOfferAdmin(ImportExportModelAdmin):
    resource_class = StudyVisaOfferResource

@admin.register(StudyVisaOfferRequirement)
class StudyVisaOfferRequirementAdmin(ImportExportModelAdmin):
    resource_class = StudyVisaOfferRequirementResource

# class CountryResource(resources.ModelResource):
#     class Meta:
#         model = Country

# class CityResource(resources.ModelResource):
#     class Meta:
#         model = City

class ProgramTypeResource(resources.ModelResource):
    class Meta:
        model = ProgramType

class AdBannerResource(resources.ModelResource):
    class Meta:
        model = AdBanner

class InstitutionResource(resources.ModelResource):
    class Meta:
        model = Institution

class CourseOfStudyResource(resources.ModelResource):
    class Meta:
        model = CourseOfStudy

# @admin.register(Country)
# class CountryAdmin(ImportExportModelAdmin):
#     resource_class = CountryResource

# @admin.register(City)
# class CityAdmin(ImportExportModelAdmin):
#     resource_class = CityResource

@admin.register(ProgramType)
class ProgramTypeAdmin(ImportExportModelAdmin):
    resource_class = ProgramTypeResource

@admin.register(Institution)
class InstitutionAdmin(ImportExportModelAdmin):
    resource_class = InstitutionResource

@admin.register(CourseOfStudy)
class CourseOfStudyAdmin(ImportExportModelAdmin):
    resource_class = CourseOfStudyResource

@admin.register(AdBanner)
class AdBannerAdmin(ImportExportModelAdmin):
    resource_class = AdBannerResource
