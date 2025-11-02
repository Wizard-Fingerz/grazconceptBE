from rest_framework import viewsets, permissions
from app.visa.study.offers.models import StudyVisaOffer
from app.visa.study.offers.serializers import StudyVisaOfferSerializer
from app.views import CustomPagination

from django.db.models import Q

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
        institution_name (case-insensitive, partial), program, course_of_study,
        and free-text search ('search') over institution, country, program,
        course_of_study, etc.
        Supports 'limit' param for limiting results.
        """
        queryset = super().get_queryset()
        country = self.request.query_params.get('country')
        institution = self.request.query_params.get('institution')
        is_active = self.request.query_params.get('is_active')
        status = self.request.query_params.get('status')
        limit = self.request.query_params.get('limit')
        institution_name = self.request.query_params.get('institution_name')
        search_term = self.request.query_params.get('search')
        program = self.request.query_params.get('program')
        course_of_study = self.request.query_params.get('course_of_study')

        if country:
            queryset = queryset.filter(country__iexact=country)
        if institution:
            # If the institution is a string (e.g., institution name or pk), 
            # try to filter by either name (FK) or pk (int). 
            try:
                # Try integer: institution pk
                institution_pk = int(institution)
                queryset = queryset.filter(institution__pk=institution_pk)
            except (ValueError, TypeError):
                # Not an int; filter by FK name
                queryset = queryset.filter(institution__name__icontains=institution)
        if institution_name:
            queryset = queryset.filter(institution__name__icontains=institution_name)
        if program:
            queryset = queryset.filter(program__icontains=program)
        if course_of_study:
            queryset = queryset.filter(course_of_study__icontains=course_of_study)
        if is_active is not None:
            true_values = ['true', '1']
            false_values = ['false', '0']
            is_active_val = is_active.strip().lower()
            if is_active_val in true_values:
                queryset = queryset.filter(is_active=True)
            elif is_active_val in false_values:
                queryset = queryset.filter(is_active=False)
        if status:
            queryset = queryset.filter(status=status)

        if search_term:
            # Remove icontains filtering on any FK that isn't a text field; search only text fields and related FK "name" field
            queryset = queryset.filter(
                Q(institution__name__icontains=search_term)
                | Q(country__icontains=search_term)
                | Q(status__icontains=search_term)
                | Q(program__icontains=search_term)
                | Q(course_of_study__icontains=search_term)
            )

        if limit is not None:
            try:
                limit_value = int(limit)
                if limit_value > 0:
                    queryset = queryset[:limit_value]
            except (ValueError, TypeError):
                pass  # Ignore invalid limit values
        return queryset

