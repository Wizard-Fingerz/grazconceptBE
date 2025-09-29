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
