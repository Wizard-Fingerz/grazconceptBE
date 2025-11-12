from rest_framework import viewsets, permissions, mixins

from app.views import CustomPagination
from .models import InvestmentPlan, InvestmentPlanBenefit, Investment
from .serializers import (
    InvestmentPlanSerializer,
    InvestmentPlanBenefitSerializer,
    InvestmentSerializer,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.response import Response

class InvestmentPlanViewSet(mixins.ListModelMixin,
                            mixins.RetrieveModelMixin,
                            viewsets.GenericViewSet):
    """
    ViewSet for listing and retrieving investment plans and their benefits.
    """
    queryset = InvestmentPlan.objects.all()
    serializer_class = InvestmentPlanSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = CustomPagination

    @action(detail=True, methods=["get"], url_path="benefits", permission_classes=[permissions.AllowAny])
    def benefits(self, request, pk=None):
        """
        List all benefits for a given investment plan.
        """
        benefits = InvestmentPlanBenefit.objects.filter(plan_id=pk).order_by('order')
        serializer = InvestmentPlanBenefitSerializer(benefits, many=True)
        return Response(serializer.data)

class InvestmentViewSet(mixins.ListModelMixin,
                        mixins.CreateModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    """
    ViewSet to list, create, and retrieve investments scoped to the current user.
    Ensures that investor is always set to the request user for all actions,
    and removes investor from incoming validated data on create.
    """
    serializer_class = InvestmentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        return Investment.objects.filter(investor=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        # Always set investor to request.user, remove investor from incoming data if present
        validated_data = dict(serializer.validated_data)
        validated_data.pop('investor', None)
        serializer.save(investor=self.request.user, **validated_data)

