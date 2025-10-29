from rest_framework import viewsets

from app.views import CustomPagination
from .models import EuropeanCitizenshipOffer, InvestmentOption
from rest_framework.permissions import IsAuthenticated
from .serializers import EuropeanCitizenshipOfferSerializer, InvestmentOptionSerializer

class EuropeanCitizenshipOfferViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows European Citizenship Offers to be viewed or edited.
    """
    queryset = EuropeanCitizenshipOffer.objects.all().order_by('-created_at')
    serializer_class = EuropeanCitizenshipOfferSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

class InvestmentOptionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Investment Options to be viewed or edited.
    """
    queryset = InvestmentOption.objects.all()
    serializer_class = InvestmentOptionSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

