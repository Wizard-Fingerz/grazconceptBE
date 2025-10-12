from rest_framework import viewsets

from rest_framework import permissions
from app.views import CustomPagination
from .models import PilgrimageOffer
from .serializers import PilgrimageOfferSerializer

class PilgrimageOfferViewSet(viewsets.ModelViewSet):
    queryset = PilgrimageOffer.objects.all()
    serializer_class = PilgrimageOfferSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination


    def get_queryset(self):
        """
        Optionally restricts the returned offers by filtering against
        query parameters in the URL. Supports 'limit' param for limiting results.
        """
        queryset = super().get_queryset()
        country = self.request.query_params.get('country')
        institution = self.request.query_params.get('institution')
        is_active = self.request.query_params.get('is_active')
        status = self.request.query_params.get('status')
        limit = self.request.query_params.get('limit')

        if country:
            queryset = queryset.filter(country=country)
        if institution:
            queryset = queryset.filter(institution=institution)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() in ['true', '1'])
        if status:
            queryset = queryset.filter(status=status)
        if limit is not None:
            try:
                limit_value = int(limit)
                if limit_value > 0:
                    queryset = queryset[:limit_value]
            except (ValueError, TypeError):
                pass  # Ignore invalid limit values
        return queryset
