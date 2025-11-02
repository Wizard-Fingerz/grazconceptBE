from rest_framework.decorators import action
from app.views import CustomPagination
from wallet.models import Wallet
from rest_framework.response import Response
from django.db import models
from rest_framework import viewsets, permissions
from .models import LoanApplication, LoanRepayment, LoanOffer
from .serializers import LoanApplicationSerializer, LoanRepaymentSerializer, LoanOfferSerializer


class LoanOfferViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling LoanOffer CRUD operations.
    Provides actions to list study loans or civil servant loans separated by loan type.
    """
    queryset = LoanOffer.objects.all()
    serializer_class = LoanOfferSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = self.queryset
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() in ['true', '1'])
        # Allow filtering by loan_type id via query param (optional)
        loan_type_id = self.request.query_params.get('loan_type')
        if loan_type_id:
            queryset = queryset.filter(loan_type=loan_type_id)
        return queryset

    @action(detail=False, methods=['get'], url_path='study-loans')
    def study_loans(self, request):
        """
        Return only loan offers of type 'Study Loan'.
        Assumes corresponding TableDropDownDefinition.label is 'Study Loan'.
        """
        study_loans = self.queryset.filter(
            loan_type__label__iexact='Study Loan'
        )
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            study_loans = study_loans.filter(is_active=is_active.lower() in ['true', '1'])

        page = self.paginate_queryset(study_loans)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(study_loans, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='civil-servant-loans')
    def civil_servant_loans(self, request):
        """
        Return only loan offers of type 'Civil Servant Loan'.
        Assumes corresponding TableDropDownDefinition.label is 'Civil Servant Loan'.
        """
        civil_servant_loans = self.queryset.filter(
            loan_type__label__iexact='Civil Servant Loan'
        )
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            civil_servant_loans = civil_servant_loans.filter(is_active=is_active.lower() in ['true', '1'])

        page = self.paginate_queryset(civil_servant_loans)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(civil_servant_loans, many=True)
        return Response(serializer.data)


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
