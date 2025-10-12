from rest_framework import viewsets
from .models import VacationOffer, VacationOfferIncludedItem, VacationOfferImage
from .serializers import (
    VacationOfferSerializer,
    VacationOfferIncludedItemSerializer,
    VacationOfferImageSerializer,
)
from rest_framework import permissions
from app.views import CustomPagination


class VacationOfferViewSet(viewsets.ModelViewSet):
    queryset = VacationOffer.objects.all()
    serializer_class = VacationOfferSerializer
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


class VacationOfferIncludedItemViewSet(viewsets.ModelViewSet):
    queryset = VacationOfferIncludedItem.objects.all()
    serializer_class = VacationOfferIncludedItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination

class VacationOfferImageViewSet(viewsets.ModelViewSet):
    queryset = VacationOfferImage.objects.all()
    serializer_class = VacationOfferImageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination
