from rest_framework import viewsets, permissions, decorators
from rest_framework.response import Response

from app.views import CustomPagination
from .models import WalletTransaction
from .serializers import WalletTransactionSerializer

class WalletTransactionViewSet(viewsets.ModelViewSet):
    queryset = WalletTransaction.objects.all()
    serializer_class = WalletTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        """
        For admin users, return all WalletTransactions (with optional filters).
        For normal users, return transactions belonging to their own wallets only.
        Supports filtering by transaction_type (exact), status (exact),
        date_from (created_at >=), date_to (created_at <=), and reference (exact).
        """
        user = self.request.user
        if user.is_staff or user.is_superuser:
            # Admin: see all transactions, but filters still apply
            queryset = WalletTransaction.objects.all().order_by('-created_at')
        else:
            queryset = WalletTransaction.objects.filter(wallet__user=user).order_by('-created_at')

        tx_type = self.request.query_params.get("transaction_type")
        status = self.request.query_params.get("status")
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        reference = self.request.query_params.get("reference")  # new filter

        if tx_type:
            queryset = queryset.filter(transaction_type=tx_type)
        if status:
            queryset = queryset.filter(status=status)
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        if reference:
            queryset = queryset.filter(reference=reference)
        return queryset


    @decorators.action(methods=['get'], detail=False, url_path='my-recent', url_name='my_recent_transactions')
    def my_recent_transactions(self, request):
        """
        Returns the recent wallet transactions for the authenticated user.
        Supports filtering by transaction_type, status, and date range via query params.
        """
        transactions = self.get_queryset()
        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(transactions, many=True)
        return Response(serializer.data)

