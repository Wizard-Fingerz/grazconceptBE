from django.db import models
from rest_framework import viewsets, permissions, decorators, response, status
from .models import Wallet
from .serializers import WalletSerializer

class WalletViewSet(viewsets.ModelViewSet):
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    @decorators.action(detail=False, methods=['get'], url_path='my-balance')
    def my_balance(self, request):
        """
        Returns the wallet balance for the authenticated user.
        GET /api/wallets/my-balance/
        """
        try:
            # Assuming each user has one wallet (or adjust logic if many)
            wallet = Wallet.objects.get(user=request.user)
        except Wallet.DoesNotExist:
            return response.Response({"detail": "Wallet not found."}, status=status.HTTP_404_NOT_FOUND)
        data = {
            "balance": wallet.balance,
            "currency": wallet.currency if hasattr(wallet, "currency") else None,
            "wallet_id": wallet.id,
        }
        return response.Response(data)


# INSERT_YOUR_CODE
from rest_framework.views import APIView

class AdminWalletAnalyticsView(APIView):
    """
    View for admin analytics on wallet metrics and transactions.
    Returns summary statistics for all wallets and wallet transactions.
    Only accessible to admins.
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        """
        Returns admin dashboard metrics including:
            - total_wallets
            - total_balance
            - avg_balance
            - currency_breakdown
            - total_transactions
            - total_deposits
            - total_withdrawals
            - total_revenue
            - pending_transactions
            - type and status summaries
        """
        from wallet.transactions.models import WalletTransaction

        wallets = Wallet.objects.all()
        total_wallets = wallets.count()
        total_balance = wallets.aggregate(total=models.Sum('balance'))['total'] or 0
        avg_balance = wallets.aggregate(avg=models.Avg('balance'))['avg'] or 0

        currency_breakdown = (
            wallets.values('currency')
            .annotate(total=models.Sum('balance'), count=models.Count('id'))
            .order_by('-total')
        )

        txns = WalletTransaction.objects.all()
        total_transactions = txns.count()

        # Total deposits
        total_deposits = (
            txns.filter(transaction_type='deposit', status='successful')
            .aggregate(total=models.Sum('amount'))['total'] or 0
        )
        # Total withdrawals
        total_withdrawals = (
            txns.filter(transaction_type='withdrawal', status='successful')
            .aggregate(total=models.Sum('amount'))['total'] or 0
        )
        # Total revenue (sum of successful 'deposit' and 'payment' transactions, or define as needed)
        total_payments = (
            txns.filter(transaction_type='payment', status='successful')
            .aggregate(total=models.Sum('amount'))['total'] or 0
        )
        total_refunds = (
            txns.filter(transaction_type='refund', status='successful')
            .aggregate(total=models.Sum('amount'))['total'] or 0
        )
        # Revenue: All incoming minus outgoing as needed; simple version: deposits + payments - withdrawals - refunds
        total_revenue = (total_deposits + total_payments) - (total_withdrawals + total_refunds)

        # Pending transactions count and list
        pending_transactions_qs = txns.filter(status='pending').order_by('-created_at')
        pending_transactions_count = pending_transactions_qs.count()
        pending_transactions_list = [
            {
                "id": t.id,
                "user_id": t.user_id,
                "wallet_id": t.wallet_id,
                "transaction_type": t.transaction_type,
                "status": t.status,
                "amount": float(t.amount),
                "currency": t.currency,
                "created_at": t.created_at,
                "reference": t.reference,
            }
            for t in pending_transactions_qs[:10]
        ]

        # By type
        type_summary = (
            txns
            .values('transaction_type')
            .annotate(count=models.Count('id'), total=models.Sum('amount'))
            .order_by('-count')
        )
        # By status
        status_summary = (
            txns
            .values('status')
            .annotate(count=models.Count('id'))
            .order_by('-count')
        )
        # Optionally: recent transactions
        recent_transactions = txns.order_by('-created_at')[:10]
        recent_list = [
            {
                "id": t.id,
                "user_id": t.user_id,
                "wallet_id": t.wallet_id,
                "transaction_type": t.transaction_type,
                "status": t.status,
                "amount": float(t.amount),
                "currency": t.currency,
                "created_at": t.created_at,
                "reference": t.reference,
            }
            for t in recent_transactions
        ]

        data = {
            "wallets": {
                "total_wallets": total_wallets,
                "total_balance": float(total_balance),
                "avg_balance": float(avg_balance),
                "currency_breakdown": list(currency_breakdown),
            },
            "transactions": {
                "total_transactions": total_transactions,
                "total_deposits": float(total_deposits),
                "total_withdrawals": float(total_withdrawals),
                "total_revenue": float(total_revenue),
                "pending_transactions": {
                    "count": pending_transactions_count,
                    "recent": pending_transactions_list,
                },
                "by_type": list(type_summary),
                "by_status": list(status_summary),
                "recent": recent_list,
            },
        }
        return response.Response(data)

