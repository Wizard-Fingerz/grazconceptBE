from rest_framework import viewsets, permissions
from .models import WalletTransaction
from .serializers import WalletTransactionSerializer

class WalletTransactionViewSet(viewsets.ModelViewSet):
    queryset = WalletTransaction.objects.all()
    serializer_class = WalletTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

