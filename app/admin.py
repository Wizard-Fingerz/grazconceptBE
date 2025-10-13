from django.contrib import admin
# Register your models here.
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from app.ad_banners.models import AdBanner
from .hotels.models import Hotel, HotelBooking, Amenity
from .flight.models import FlightBooking
from .visa.study.institutions.models import ProgramType, Institution, CourseOfStudy
from .visa.study.offers.models import StudyVisaOffer, StudyVisaOfferRequirement
from .visa.study.models import StudyVisaApplication  # <-- Include StudyVisaApplication
# Import WorkVisaOffer, WorkOrganization, and WorkVisaOfferRequirement and WorkVisaApplication
from .visa.work.offers.models import WorkVisaOffer, WorkVisaOfferRequirement, WorkVisaApplication
from .visa.work.organization.models import WorkOrganization
# Import VacationOffer, VacationOfferIncludedItem, VacationOfferImage
from .visa.vacation.offer.models import VacationOffer, VacationOfferIncludedItem, VacationOfferImage

# Import PilgrimageOffer, PilgrimageOfferIncludedItem, PilgrimageOfferImage, PilgrimageVisaApplication
from .visa.pilgrimage.offer.models import (
    PilgrimageOffer,
    PilgrimageOfferIncludedItem,
    PilgrimageOfferImage,
    PilgrimageVisaApplication,  # Include PilgrimageVisaApplication
)

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

class StudyVisaApplicationResource(resources.ModelResource):
    class Meta:
        model = StudyVisaApplication

class WorkVisaOfferResource(resources.ModelResource):
    class Meta:
        model = WorkVisaOffer

class WorkVisaOfferRequirementResource(resources.ModelResource):
    class Meta:
        model = WorkVisaOfferRequirement

class WorkVisaApplicationResource(resources.ModelResource):
    class Meta:
        model = WorkVisaApplication

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

class PilgrimageOfferResource(resources.ModelResource):
    class Meta:
        model = PilgrimageOffer

class PilgrimageOfferIncludedItemResource(resources.ModelResource):
    class Meta:
        model = PilgrimageOfferIncludedItem

class PilgrimageOfferImageResource(resources.ModelResource):
    class Meta:
        model = PilgrimageOfferImage

class PilgrimageVisaApplicationResource(resources.ModelResource):
    class Meta:
        model = PilgrimageVisaApplication

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

@admin.register(StudyVisaApplication)
class StudyVisaApplicationAdmin(ImportExportModelAdmin):
    resource_class = StudyVisaApplicationResource

@admin.register(WorkVisaOffer)
class WorkVisaOfferAdmin(ImportExportModelAdmin):
    resource_class = WorkVisaOfferResource

@admin.register(WorkVisaOfferRequirement)
class WorkVisaOfferRequirementAdmin(ImportExportModelAdmin):
    resource_class = WorkVisaOfferRequirementResource

@admin.register(WorkVisaApplication)
class WorkVisaApplicationAdmin(ImportExportModelAdmin):
    resource_class = WorkVisaApplicationResource

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

@admin.register(PilgrimageOffer)
class PilgrimageOfferAdmin(ImportExportModelAdmin):
    resource_class = PilgrimageOfferResource

@admin.register(PilgrimageOfferIncludedItem)
class PilgrimageOfferIncludedItemAdmin(ImportExportModelAdmin):
    resource_class = PilgrimageOfferIncludedItemResource

@admin.register(PilgrimageOfferImage)
class PilgrimageOfferImageAdmin(ImportExportModelAdmin):
    resource_class = PilgrimageOfferImageResource

@admin.register(PilgrimageVisaApplication)
class PilgrimageVisaApplicationAdmin(ImportExportModelAdmin):
    resource_class = PilgrimageVisaApplicationResource

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
