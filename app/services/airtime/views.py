from rest_framework import viewsets, permissions, status
from rest_framework.response import Response

from app.views import CustomPagination
from .models import NetworkProvider, AirtimePurchase, DataPlan, DataPurchase
from .serializers import (
    NetworkProviderSerializer,
    AirtimePurchaseSerializer,
    DataPlanSerializer,
    DataPurchaseSerializer,
)
import requests
from django.conf import settings
from rest_framework.decorators import action

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
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return AirtimePurchase.objects.all()
        return AirtimePurchase.objects.filter(user=user)

    def perform_create(self, serializer):
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


class DataPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint to list data plans available for purchase.
    Includes custom action to get all providers with any data plans.
    """
    queryset = DataPlan.objects.all().select_related("provider")
    serializer_class = DataPlanSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = CustomPagination

    def get_queryset(self):
        qs = super().get_queryset()
        provider_id = self.request.query_params.get("provider_id")
        if provider_id:
            qs = qs.filter(provider_id=provider_id)
        return qs

    @action(detail=False, methods=["get"], url_path="providers-with-plans", permission_classes=[permissions.AllowAny])
    def providers_with_plans(self, request):
        """
        Returns a list of providers that have at least one data plan.
        """
        provider_ids = DataPlan.objects.values_list("provider_id", flat=True).distinct()
        providers = NetworkProvider.objects.filter(id__in=provider_ids, active=True)
        serializer = NetworkProviderSerializer(providers, many=True)
        return Response(serializer.data)

class DataPurchaseViewSet(viewsets.ModelViewSet):
    """
    API endpoint for creating and viewing Data plan purchases.
    """
    queryset = DataPurchase.objects.all()
    serializer_class = DataPurchaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return DataPurchase.objects.all()
        return DataPurchase.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        The provider API call is now handled in signals.py pre_save and wallet debit in post_save.
        This view just creates the data purchase.
        """
        data = request.data.copy()
        data["user"] = request.user.pk

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers_out = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers_out)
