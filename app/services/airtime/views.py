from rest_framework import viewsets, permissions, status
from rest_framework.response import Response

from app.views import CustomPagination
from .models import NetworkProvider, AirtimePurchase
from .serializers import NetworkProviderSerializer, AirtimePurchaseSerializer
import requests
from django.conf import settings



class NetworkProviderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows network providers to be viewed.
    """
    queryset = NetworkProvider.objects.filter(active=True)
    serializer_class = NetworkProviderSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = CustomPagination


class AirtimePurchaseViewSet(viewsets.ModelViewSet):
    """
    API endpoint for creating and viewing Airtime purchases.
    """
    queryset = AirtimePurchase.objects.all()
    serializer_class = AirtimePurchaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        # Only return purchases for the logged-in user
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return AirtimePurchase.objects.all()
        return AirtimePurchase.objects.filter(user=user)

    def perform_create(self, serializer):
        # Ensure that logged-in user is associated with the purchase
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        The provider API call is now handled in signals.py pre_save and wallet debit in post_save.
        This view just creates the purchase.
        """
        data = request.data.copy()
        data["user"] = request.user.pk

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers_out = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers_out)

