from rest_framework import viewsets, permissions
from app.visa.study.offers.models import StudyVisaOffer
from app.visa.study.offers.serializers import StudyVisaOfferSerializer
from app.views import CustomPagination


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
        """
        queryset = super().get_queryset()
        country = self.request.query_params.get('country')
        institution = self.request.query_params.get('institution')
        is_active = self.request.query_params.get('is_active')
        status = self.request.query_params.get('status')

        if country:
            queryset = queryset.filter(country=country)
        if institution:
            queryset = queryset.filter(institution=institution)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() in ['true', '1'])
        if status:
            queryset = queryset.filter(status=status)
        return queryset
