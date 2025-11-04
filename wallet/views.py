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
