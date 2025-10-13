from rest_framework import viewsets, permissions
from .models import PaymentGateway, PaymentGatewayCallbackLog
from .serializers import PaymentGatewaySerializer, PaymentGatewayCallbackLogSerializer

class PaymentGatewayViewSet(viewsets.ModelViewSet):
    queryset = PaymentGateway.objects.all()
    serializer_class = PaymentGatewaySerializer
    permission_classes = [permissions.IsAuthenticated]

class PaymentGatewayCallbackLogViewSet(viewsets.ModelViewSet):
    queryset = PaymentGatewayCallbackLog.objects.all()
    serializer_class = PaymentGatewayCallbackLogSerializer
    permission_classes = [permissions.IsAuthenticated]

