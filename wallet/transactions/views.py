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

    @decorators.action(methods=['get'], detail=False, url_path='my-recent', url_name='my_recent_transactions')
    def my_recent_transactions(self, request):
        """
        Returns the recent wallet transactions for the authenticated user.
        """
        # Get the requesting user's wallet transactions, most recent first
        transactions = WalletTransaction.objects.filter(wallet__user=request.user).order_by('-created_at')
        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(transactions, many=True)
        return Response(serializer.data)

