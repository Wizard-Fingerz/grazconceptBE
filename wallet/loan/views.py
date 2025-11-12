from rest_framework.decorators import action
from app.views import CustomPagination
from wallet.models import Wallet
from rest_framework.response import Response
from django.db import models
from rest_framework import viewsets, permissions
from .models import LoanApplication, LoanRepayment, LoanOffer
from .serializers import LoanApplicationSerializer, LoanRepaymentSerializer, LoanOfferSerializer

# Import actual model for loan_type
from definition.models import TableDropDownDefinition

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
        Assumes corresponding TableDropDownDefinition.term is 'Study Loan'.
        """
        # Find the TableDropDownDefinition object with term="Study Loan"
        study_loan_type = TableDropDownDefinition.objects.filter(term__iexact='Study Loan').first()
        if not study_loan_type:
            # No study loan type found, return empty response
            study_loans = LoanOffer.objects.none()
        else:
            study_loans = self.queryset.filter(
                loan_type=study_loan_type
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
        Assumes corresponding TableDropDownDefinition.term is 'Civil Servant Loan'.
        """
        civil_servant_type = TableDropDownDefinition.objects.filter(term__iexact='Civil Servant').first()
        if not civil_servant_type:
            civil_servant_loans = LoanOffer.objects.none()
        else:
            civil_servant_loans = self.queryset.filter(
                loan_type=civil_servant_type
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

    def create(self, request, *args, **kwargs):
        """
        Override create to set user as request.user and include user in the request data for the serializer.
        """
        data = request.data.copy()
        data['user'] = request.user.pk  # Add user to the request data
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)  # No need to pass user; it is in the data
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer, user=None):
        # Set the user to the authenticated user on creation
        serializer.save(user=user or self.request.user)


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
    total loan amount, total amount paid, wallet balance, and recent transactions.
    """
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def summary(self, request):
        user = request.user

        # Total loan amount applied for and approved/disbursed/repaid, etc.
        total_loan_amount = LoanApplication.objects.filter(user=user).aggregate(
            total=models.Sum('amount')
        )['total'] or 0.00

        # Total amount paid across all repayments
        total_paid = LoanRepayment.objects.filter(user=user).aggregate(
            total=models.Sum('amount')
        )['total'] or 0.00

        # Wallet balance (if wallet exists)
        wallet = getattr(user, 'wallet', None)
        wallet_balance = wallet.balance if wallet else 0.00

        currency = wallet.currency if wallet else "NGN"

        # Fetch the recent loan application (most recent one)
        recent_loan_application = (
            LoanApplication.objects.filter(user=user).order_by('-created_at').first()
        )
        recent_loan_application_data = None
        if recent_loan_application:
            recent_loan_application_data = {
                'id': recent_loan_application.id,
                'amount': float(recent_loan_application.amount),
                'status': getattr(recent_loan_application, 'status', None),
                'created_at': recent_loan_application.created_at,
            }

        # Fetch the recent loan repayment (most recent one)
        recent_loan_repayment = (
            LoanRepayment.objects.filter(user=user).order_by('-created_at').first()
        )
        recent_loan_repayment_data = None
        if recent_loan_repayment:
            recent_loan_repayment_data = {
                'id': recent_loan_repayment.id,
                'amount': float(recent_loan_repayment.amount),
                'status': getattr(recent_loan_repayment, 'status', None),
                'created_at': recent_loan_repayment.created_at,
            }

        # Fetch the most recent wallet transaction, if model is available
        recent_wallet_transaction_data = None
        try:
            from wallet.transactions.models import WalletTransaction
            recent_wallet_transaction = (
                WalletTransaction.objects.filter(wallet=wallet).order_by('-created_at').first()
                if wallet else None
            )
            if recent_wallet_transaction:
                recent_wallet_transaction_data = {
                    'id': recent_wallet_transaction.id,
                    'amount': float(getattr(recent_wallet_transaction, 'amount', 0)),
                    'type': getattr(recent_wallet_transaction, 'transaction_type', None),
                    'created_at': recent_wallet_transaction.created_at,
                    'status': getattr(recent_wallet_transaction, 'status', None),
                }
        except Exception:
            recent_wallet_transaction_data = None

        return Response({
            'total_loan_amount': float(total_loan_amount),
            'total_amount_paid': float(total_paid),
            'wallet_balance': float(wallet_balance),
            'currency': currency,
            'recent_loan_application': recent_loan_application_data,
            'recent_loan_repayment': recent_loan_repayment_data,
            'recent_wallet_transaction': recent_wallet_transaction_data
        })
