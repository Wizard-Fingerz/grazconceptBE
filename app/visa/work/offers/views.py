from rest_framework import viewsets
from app.views import CustomPagination
from app.visa.work.offers.models import WorkVisaOffer
from rest_framework import serializers
from rest_framework import permissions
from app.visa.work.offers.serializers import WorkVisaOfferSerializer



class WorkVisaOfferViewSet(viewsets.ModelViewSet):
    queryset = WorkVisaOffer.objects.all()
    serializer_class = WorkVisaOfferSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination

