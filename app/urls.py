from django.urls import path, include
from rest_framework.routers import DefaultRouter

from app.ad_banners.views import AdBannerViewSet
from app.citizenship.european.views import EuropeanCitizenshipOfferViewSet, InvestmentOptionViewSet
from app.help_center.support_ticket.views import SupportTicketViewSet
from app.visa.pilgrimage.offer.views import (
    PilgrimageOfferViewSet,
    PilgrimageVisaApplicationViewSet,
    PilgrimageVisaApplicationCommentViewSet,
)
from app.visa.study.offers.views import StudyVisaOfferViewSet
from app.visa.study.views import StudyVisaApplicationAnalyticsView, StudyVisaApplicationViewSet, StudyVisaApplicationCommentViewSet
from app.visa.vacation.offer.views import (
    VacationOfferViewSet,
    VacationVisaApplicationViewSet,
)
from app.visa.vacation.offer.views import VacationVisaApplicationCommentViewSet  # <-- register vacation visa comment viewset separately for custom routes
from app.visa.work.offers.views import (
    WorkVisaOfferViewSet,
    WorkVisaApplicationViewSet,
    # InterviewFAQViewSet,
    WorkVisaInterviewViewSet,
    CVSubmissionViewSet,
    WorkVisaApplicationCommentViewSet,
)
from app.visa.work.organization.views import WorkOrganizationViewSet
from .flight.views import get_booked_flights, search_flights, suggest_flights_for_user, suggest_locations
from .hotels.views import HotelBookingViewSet, HotelViewSet
from .visa.study.institutions.views import (
    # CountryViewSet,
    # CityViewSet,
    ProgramTypeViewSet,
    InstitutionViewSet,
    CourseOfStudyViewSet,
)
# --- Import Education/Exam Fee ViewSets ---
from app.services.edu_and_exam_fee.views import (
    EducationFeeProviderViewSet,
    EducationFeeTypeViewSet,
    EducationFeePaymentViewSet,
)
# --- Import Knowledge Base FAQ ViewSet ---
from app.help_center.knowledge_base.views import FaqArticleViewSet

# ---- Investment endpoints from app.citizenship.investment.views ----
from app.citizenship.investment.views import (
    InvestmentPlanViewSet,
    InvestmentViewSet,
)

# --- Import CVProfileViewSet for CV builder API ---
from app.cv_builder.views import CVProfileViewSet

# --- Import Airtime API viewsets ---
from app.services.airtime.views import (
    NetworkProviderViewSet,
    AirtimePurchaseViewSet,
    DataPlanViewSet,
    DataPurchaseViewSet,
)

# --- Import Utility API viewsets ---
from app.services.utility.views import (
    UtilityProviderViewSet,
    UtilityBillPaymentViewSet,
)

router = DefaultRouter()
router.register(r'hotel-bookings', HotelBookingViewSet, basename='hotelbooking')
router.register(r'hotels', HotelViewSet, basename='hotels')
# router.register(r'countries', CountryViewSet, basename='countries')
# router.register(r'cities', CityViewSet, basename='cities')
router.register(r'program-types', ProgramTypeViewSet, basename='programtypes')
router.register(r'institutions', InstitutionViewSet, basename='institutions')
router.register(r'courses-of-study', CourseOfStudyViewSet, basename='coursesofstudy')
router.register(r'study-visa-application', StudyVisaApplicationViewSet, basename='studyvisaapplication')
router.register(r'study-visa-application-comments', StudyVisaApplicationCommentViewSet, basename='studyvisaapplicationcomment')
router.register(r'ad-banner', AdBannerViewSet, basename='adbanner')
router.register(r'study-visa-offers', StudyVisaOfferViewSet, basename='studyvisaoffers')
router.register(r'work-visa-offers', WorkVisaOfferViewSet, basename='workvisaoffers')
router.register(r'work-visa-application', WorkVisaApplicationViewSet, basename='workvisaapplication')
router.register(r'work-visa-application-comments', WorkVisaApplicationCommentViewSet, basename='workvisaapplicationcomment')
router.register(r'work-organisations', WorkOrganizationViewSet, basename='workvisaorg')
router.register(r'vacation-offer', VacationOfferViewSet, basename='vacation-offer')
router.register(r'vacation-application', VacationVisaApplicationViewSet, basename='vacationapplication')
router.register(r'vacation-visa-application-comments', VacationVisaApplicationCommentViewSet, basename='vacationvisaapplicationcomment')  # <-- register vacation visa application comments viewset/route
router.register(r'pilgrimage-offer', PilgrimageOfferViewSet, basename='pilgrimageoffer')
router.register(r'pilgrimage-application', PilgrimageVisaApplicationViewSet, basename='pilgrimageapplication')
router.register(r'pilgrimage-application-comments', PilgrimageVisaApplicationCommentViewSet, basename='pilgrimageapplicationcomment')
router.register(r'european-citizenship-offer', EuropeanCitizenshipOfferViewSet, basename='europiancitizenshipoffer')
router.register(r'investment-plans', InvestmentPlanViewSet, basename='investmentplan')
router.register(r'investments', InvestmentViewSet, basename='investment')
router.register(r'investment-options', InvestmentOptionViewSet, basename='investmentoptions')

# --- Register Work Visa Interview & FAQ endpoints ---
router.register(r'work-visa-interviews', WorkVisaInterviewViewSet, basename='workvisainterviews')
# router.register(r'work-visa-faq', InterviewFAQViewSet, basename='workvisafaq')
router.register(r'cv-submission', CVSubmissionViewSet, basename='cvsubmission')
# ----------------------------------------------------

# --- Register Education/Exam Fee endpoints ---
router.register(r'education-fee-providers', EducationFeeProviderViewSet, basename='educationfeecproviders')
router.register(r'education-fee-types', EducationFeeTypeViewSet, basename='educationfeetypes')
router.register(r'education-fee-payments', EducationFeePaymentViewSet, basename='educationfeepayments')
# --------------------------------------------

# --- Register Knowledge Base FAQ endpoints ---
router.register(r'faq-articles', FaqArticleViewSet, basename='faqarticles')
router.register(r'support-ticket', SupportTicketViewSet, basename='supportticket')
# --------------------------------------------

# --- Register CV Builder endpoints ---
router.register(r'cv-profiles', CVProfileViewSet, basename='cvprofile')

# --- Register Airtime API endpoints ---
router.register(r'airtime-network-providers', NetworkProviderViewSet, basename='airtime-network-providers')
router.register(r'airtime-purchases', AirtimePurchaseViewSet, basename='airtime-purchases')
router.register(r'airtime-data-plans', DataPlanViewSet, basename='airtime-data-plans')
router.register(r'airtime-data-purchases', DataPurchaseViewSet, basename='airtime-data-purchases')

# --- Register Utility API endpoints ---
router.register(r'utility-providers', UtilityProviderViewSet, basename='utility-providers')
router.register(r'utility-bill-payments', UtilityBillPaymentViewSet, basename='utility-bill-payments')

urlpatterns = [
    path("search-flights/", search_flights, name="search_flights"),
    path("booked-flights/", get_booked_flights, name="get_booked_flights"),
    path("suggest-flights/", suggest_flights_for_user, name="suggest_flights_for_user"),
    path("suggest-locations/", suggest_locations, name="suggest_locations"),
    path("", include(router.urls)),

   
    path(
        "study-visa-application-analytics/",
        StudyVisaApplicationAnalyticsView.as_view(),
        name="study_visa_application_analytics"
    ),


]
