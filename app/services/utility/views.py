from rest_framework import viewsets, permissions
from .models import UtilityProvider, UtilityBillPayment
from .serializers import UtilityProviderSerializer, UtilityBillPaymentSerializer

class UtilityProviderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows utility providers to be viewed.
    """
    queryset = UtilityProvider.objects.all()
    serializer_class = UtilityProviderSerializer
    permission_classes = [permissions.AllowAny]

class UtilityBillPaymentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows utility bill payments to be created and viewed.
    """
    queryset = UtilityBillPayment.objects.all()
    serializer_class = UtilityBillPaymentSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

    def perform_create(self, serializer):
        # Automatically associate payment with the current user, if authenticated
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save()
