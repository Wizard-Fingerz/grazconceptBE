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
