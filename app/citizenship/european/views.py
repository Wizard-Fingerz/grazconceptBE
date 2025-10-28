from rest_framework import viewsets

from app.views import CustomPagination
from .models import EuropeanCitizenshipOffer
from rest_framework.permissions import IsAuthenticated
from .serializers import EuropeanCitizenshipOfferSerializer

class EuropeanCitizenshipOfferViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows European Citizenship Offers to be viewed or edited.
    """
    queryset = EuropeanCitizenshipOffer.objects.all().order_by('-created_at')
    serializer_class = EuropeanCitizenshipOfferSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]


