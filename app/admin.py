from django.contrib import admin
# Register your models here.
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from app.ad_banners.models import AdBanner
from .hotels.models import Hotel, HotelBooking, Amenity
from .flight.models import FlightBooking
from .visa.study.institutions.models import ProgramType, Institution, CourseOfStudy
from .visa.study.offers.models import StudyVisaOffer, StudyVisaOfferRequirement
from .visa.study.models import StudyVisaApplication
from .visa.work.offers.models import (
    WorkVisaOffer,
    WorkVisaOfferRequirement,
    WorkVisaApplication,
    InterviewFAQ,
    WorkVisaInterview,
)
from .visa.work.organization.models import WorkOrganization
from .visa.vacation.offer.models import (
    VacationOffer,
    VacationOfferIncludedItem,
    VacationOfferImage,
    VacationVisaApplication,
)
from .visa.pilgrimage.offer.models import (
    PilgrimageOffer,
    PilgrimageOfferIncludedItem,
    PilgrimageOfferImage,
    PilgrimageVisaApplication,
)

# --- European Citizenship Admin Imports ---
from .citizenship.european.models import EuropeanCitizenshipOffer, InvestmentOption

# --- Education/Exam Fee Admin Imports ---
from .services.edu_and_exam_fee.models import (
    EducationFeeProvider,
    EducationFeeType,
    EducationFeePayment,
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

class InterviewFAQResource(resources.ModelResource):
    class Meta:
        model = InterviewFAQ

class WorkVisaInterviewResource(resources.ModelResource):
    class Meta:
        model = WorkVisaInterview

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

class VacationVisaApplicationResource(resources.ModelResource):
    class Meta:
        model = VacationVisaApplication

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

# --- European Citizenship Resource ---
class EuropeanCitizenshipOfferResource(resources.ModelResource):
    class Meta:
        model = EuropeanCitizenshipOffer

class InvestmentOptionResource(resources.ModelResource):
    class Meta:
        model = InvestmentOption

# --- Education/Exam Fee Resources ---
class EducationFeeProviderResource(resources.ModelResource):
    class Meta:
        model = EducationFeeProvider

class EducationFeeTypeResource(resources.ModelResource):
    class Meta:
        model = EducationFeeType

class EducationFeePaymentResource(resources.ModelResource):
    class Meta:
        model = EducationFeePayment

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

@admin.register(InterviewFAQ)
class InterviewFAQAdmin(ImportExportModelAdmin):
    resource_class = InterviewFAQResource

@admin.register(WorkVisaInterview)
class WorkVisaInterviewAdmin(ImportExportModelAdmin):
    resource_class = WorkVisaInterviewResource

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

@admin.register(VacationVisaApplication)
class VacationVisaApplicationAdmin(ImportExportModelAdmin):
    resource_class = VacationVisaApplicationResource

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

# --- European Citizenship Admin Registration ---
@admin.register(EuropeanCitizenshipOffer)
class EuropeanCitizenshipOfferAdmin(ImportExportModelAdmin):
    resource_class = EuropeanCitizenshipOfferResource

@admin.register(InvestmentOption)
class InvestmentOptionAdmin(ImportExportModelAdmin):
    resource_class = InvestmentOptionResource

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
    list_filter = ['city', 'country']  # Add city and country filtering

@admin.register(CourseOfStudy)
class CourseOfStudyAdmin(ImportExportModelAdmin):
    resource_class = CourseOfStudyResource
    list_filter = ['institution', 'program_type']  # Add filters for related institution and program type

@admin.register(AdBanner)
class AdBannerAdmin(ImportExportModelAdmin):
    resource_class = AdBannerResource

# --- Education/Exam Fee Admin Registration ---
@admin.register(EducationFeeProvider)
class EducationFeeProviderAdmin(ImportExportModelAdmin):
    resource_class = EducationFeeProviderResource

@admin.register(EducationFeeType)
class EducationFeeTypeAdmin(ImportExportModelAdmin):
    resource_class = EducationFeeTypeResource

@admin.register(EducationFeePayment)
class EducationFeePaymentAdmin(ImportExportModelAdmin):
    resource_class = EducationFeePaymentResource
