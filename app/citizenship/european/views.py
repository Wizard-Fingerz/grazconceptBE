from rest_framework import viewsets
from .models import EuropeanCitizenshipOffer
from .serializers import EuropeanCitizenshipOfferSerializer

class EuropeanCitizenshipOfferViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows European Citizenship Offers to be viewed or edited.
    """
    queryset = EuropeanCitizenshipOffer.objects.all().order_by('-created_at')
    serializer_class = EuropeanCitizenshipOfferSerializer

