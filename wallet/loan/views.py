from rest_framework.decorators import action
from wallet.models import Wallet
from rest_framework.response import Response
from django.db import models
from rest_framework import viewsets, permissions
from .models import LoanApplication, LoanRepayment
from .serializers import LoanApplicationSerializer, LoanRepaymentSerializer


class LoanApplicationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling LoanApplication CRUD operations.
    """
    queryset = LoanApplication.objects.all()
    serializer_class = LoanApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only return loan applications related to the authenticated user
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Set the user to the authenticated user on creation
        serializer.save(user=self.request.user)


class LoanRepaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling LoanRepayment CRUD operations.
    """
    queryset = LoanRepayment.objects.all()
    serializer_class = LoanRepaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only return repayments related to the authenticated user
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Set the user to the authenticated user on creation
        serializer.save(user=self.request.user)

        # INSERT_YOUR_CODE


class LoanAnalyticsViewSet(viewsets.ViewSet):
    """
    A simple ViewSet for returning loan analytics for the current user: 
    total loan amount, total amount paid, and wallet balance.
    """
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def summary(self, request):
        user = request.user

        # Total loan amount applied for and approved/disbursed/repaid, etc.
        total_loan_amount = LoanApplication.objects.filter(user=user).aggregate(
            total=models.Sum('amount')
        )['total'] or 0

        # Total amount paid across all repayments
        total_paid = LoanRepayment.objects.filter(user=user).aggregate(
            total=models.Sum('amount')
        )['total'] or 0

        # Wallet balance (if wallet exists)
        wallet = getattr(user, 'wallet', None)
        wallet_balance = wallet.balance if wallet else 0

        currency = wallet.currency if wallet else "NGN"

        return Response({
            'total_loan_amount': total_loan_amount,
            'total_amount_paid': total_paid,
            'wallet_balance': wallet_balance,
            'currency': currency,
        })


