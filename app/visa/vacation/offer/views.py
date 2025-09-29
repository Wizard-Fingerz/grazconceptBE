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
