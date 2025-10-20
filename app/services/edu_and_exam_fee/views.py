from rest_framework import viewsets
from .models import EducationFeeProvider, EducationFeeType, EducationFeePayment
from .serializers import (
    EducationFeeProviderSerializer,
    EducationFeeTypeSerializer,
    EducationFeePaymentSerializer,
)


class EducationFeeProviderViewSet(viewsets.ModelViewSet):
    queryset = EducationFeeProvider.objects.all()
    serializer_class = EducationFeeProviderSerializer


class EducationFeeTypeViewSet(viewsets.ModelViewSet):
    queryset = EducationFeeType.objects.all()
    serializer_class = EducationFeeTypeSerializer


class EducationFeePaymentViewSet(viewsets.ModelViewSet):
    queryset = EducationFeePayment.objects.all()
    serializer_class = EducationFeePaymentSerializer

