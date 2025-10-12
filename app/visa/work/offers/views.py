from rest_framework import viewsets
from rest_framework import permissions
from app.views import CustomPagination
from app.visa.work.offers.models import WorkVisaOffer, WorkVisaApplication
from app.visa.work.offers.serializers import WorkVisaOfferSerializer, WorkVisaApplicationSerializer


class WorkVisaOfferViewSet(viewsets.ModelViewSet):
    queryset = WorkVisaOffer.objects.all()
    serializer_class = WorkVisaOfferSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination


class WorkVisaApplicationViewSet(viewsets.ModelViewSet):
    queryset = WorkVisaApplication.objects.all()
    serializer_class = WorkVisaApplicationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination

