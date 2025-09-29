from django.contrib import admin

# Register your models here.
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from app.ad_banners.models import AdBanner

from .hotels.models import Hotel, HotelBooking, Amenity
from .flight.models import FlightBooking
from .visa.study.institutions.models import ProgramType, Institution, CourseOfStudy
from .visa.study.offers.models import StudyVisaOffer, StudyVisaOfferRequirement

# Import WorkVisaOffer, WorkOrganization, and WorkVisaOfferRequirement
from .visa.work.offers.models import WorkVisaOffer, WorkVisaOfferRequirement
from .visa.work.organization.models import WorkOrganization

# Import VacationOffer, VacationOfferIncludedItem, VacationOfferImage
from .visa.vacation.offer.models import VacationOffer, VacationOfferIncludedItem, VacationOfferImage

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

class WorkVisaOfferResource(resources.ModelResource):
    class Meta:
        model = WorkVisaOffer

class WorkVisaOfferRequirementResource(resources.ModelResource):
    class Meta:
        model = WorkVisaOfferRequirement

class WorkOrganizationResource(resources.ModelResource):
    class Meta:
        model = WorkOrganization

class VacationOfferResource(resources.ModelResource):
    class Meta:
        model = VacationOffer

class VacationOfferIncludedItemResource(resources.ModelResource):
    class Meta:
        model = VacationOfferIncludedItem

class VacationOfferImageResource(resources.ModelResource):
    class Meta:
        model = VacationOfferImage

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

@admin.register(WorkVisaOffer)
class WorkVisaOfferAdmin(ImportExportModelAdmin):
    resource_class = WorkVisaOfferResource

@admin.register(WorkVisaOfferRequirement)
class WorkVisaOfferRequirementAdmin(ImportExportModelAdmin):
    resource_class = WorkVisaOfferRequirementResource

@admin.register(WorkOrganization)
class WorkOrganizationAdmin(ImportExportModelAdmin):
    resource_class = WorkOrganizationResource

@admin.register(VacationOffer)
class VacationOfferAdmin(ImportExportModelAdmin):
    resource_class = VacationOfferResource

@admin.register(VacationOfferIncludedItem)
class VacationOfferIncludedItemAdmin(ImportExportModelAdmin):
    resource_class = VacationOfferIncludedItemResource

@admin.register(VacationOfferImage)
class VacationOfferImageAdmin(ImportExportModelAdmin):
    resource_class = VacationOfferImageResource

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
