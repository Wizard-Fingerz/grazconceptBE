from rest_framework import viewsets, permissions, mixins

from app.views import CustomPagination
from .models import InvestmentPlan, InvestmentPlanBenefit, Investment
from .serializers import (
    InvestmentPlanSerializer,
    InvestmentPlanBenefitSerializer,
    InvestmentSerializer,
)
from rest_framework.permissions import IsAuthenticated
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
    Ensures that investor is always set to the request user for all actions.
    """
    serializer_class = InvestmentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        return Investment.objects.filter(investor=self.request.user).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        """
        Ensure investor is always set to the request user when creating an investment.
        Catch any wallet balance ValidationError and return as a normal error message.
        """
        from django.core.exceptions import ValidationError as DjangoValidationError

        data = request.data.copy()
        data['investor'] = request.user.id
        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=201, headers=headers)
        except DjangoValidationError as e:
            detail = e.messages if hasattr(e, "messages") else [str(e)]
            # Remove 'success': False and respond with standard error keys as dictated by DRF (but as 400)
            return Response(
                # {
                #     "error": detail[0] if detail else "Validation failed.",
                #     "errors": detail,
                # },

                detail,
                status=400
            )
