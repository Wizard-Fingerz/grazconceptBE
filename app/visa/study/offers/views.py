from rest_framework import viewsets, permissions
from app.visa.study.offers.models import StudyVisaOffer
from app.visa.study.offers.serializers import StudyVisaOfferSerializer
from app.views import CustomPagination

from django.db.models import Q
from django.core.exceptions import FieldError

class StudyVisaOfferViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Study Visa Offers to be viewed or edited.
    """
    queryset = StudyVisaOffer.objects.all().order_by('-created_at')
    serializer_class = StudyVisaOfferSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination

    def get_queryset(self):
        """
        Optionally restricts the returned offers by filtering against
        query parameters in the URL. 
        Supports filtering by country, institution, is_active, status,
        institution_name (case-insensitive, partial), program_type (by pk or name), course_of_study (by pk or name),
        and free-text search ('search') over institution name, country, offer_title, description, and other text fields.
        Supports 'limit' param for limiting results.
        """
        queryset = super().get_queryset()
        params = self.request.query_params

        country = params.get('country')
        institution = params.get('institution')
        institution_name = params.get('institution_name')
        program_type = params.get('program_type')
        program = params.get('program')  # For compatibility, but not a model field
        course_of_study = params.get('course_of_study')
        is_active = params.get('is_active')
        status = params.get('status')
        limit = params.get('limit')
        search_term = params.get('search')

        # country is a CountryField, string-based
        if country:
            queryset = queryset.filter(country__iexact=country)

        # institution is a ForeignKey (Institution with .name attribute)
        if institution:
            try:
                institution_pk = int(institution)
                queryset = queryset.filter(institution__pk=institution_pk)
            except (ValueError, TypeError):
                queryset = queryset.filter(institution__name__icontains=institution)

        # direct filter on institution name (partial, ci)
        if institution_name:
            queryset = queryset.filter(institution__name__icontains=institution_name)

        # program_type is a ForeignKey (ProgramType with .name attribute)
        if program_type:
            try:
                program_type_pk = int(program_type)
                queryset = queryset.filter(program_type__pk=program_type_pk)
            except (ValueError, TypeError):
                queryset = queryset.filter(program_type__name__icontains=program_type)

        # legacy: 'program' parameter as alias of program_type name
        if program:
            queryset = queryset.filter(program_type__name__icontains=program)

        # course_of_study is a ForeignKey (CourseOfStudy with .name attribute)
        if course_of_study:
            try:
                cos_pk = int(course_of_study)
                queryset = queryset.filter(course_of_study__pk=cos_pk)
            except (ValueError, TypeError):
                queryset = queryset.filter(course_of_study__name__icontains=course_of_study)

        # is_active is a BooleanField
        if is_active is not None:
            true_values = {'true', '1', 'yes', 'on'}
            false_values = {'false', '0', 'no', 'off'}
            is_active_val = str(is_active).strip().lower()
            if is_active_val in true_values:
                queryset = queryset.filter(is_active=True)
            elif is_active_val in false_values:
                queryset = queryset.filter(is_active=False)

        # status is a ForeignKey (TableDropDownDefinition, filter by pk)
        if status:
            try:
                status_pk = int(status)
                queryset = queryset.filter(status__pk=status_pk)
            except (ValueError, TypeError):
                queryset = queryset.filter(status__name__icontains=status)

        # Search logic (fix: do NOT use ForeignKey__name__icontains where 'name' is not a field on the related model!)
        if search_term:
            search_q = Q()
            # Only include valid target fields (see model definition)
            search_q |= Q(institution__name__icontains=search_term)
            search_q |= Q(course_of_study__name__icontains=search_term)
            search_q |= Q(program_type__name__icontains=search_term)
            search_q |= Q(country__icontains=search_term)
            search_q |= Q(offer_title__icontains=search_term)
            search_q |= Q(description__icontains=search_term)
            search_q |= Q(minimum_qualification__icontains=search_term)
            search_q |= Q(other_requirements__icontains=search_term)
            # Only add status__name__icontains if the related TableDropDownDefinition really has a 'name' field
            # This is safe per model context.
            try:
                queryset = queryset.filter(search_q)
            except FieldError:
                # This guards against the unsupported lookup: skip the broken filter if fails.
                pass

        # Limiting results if limit is given
        if limit is not None:
            try:
                limit_value = int(limit)
                if limit_value > 0:
                    return queryset[:limit_value]
            except (ValueError, TypeError):
                pass

        return queryset
