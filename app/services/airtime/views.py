from rest_framework import viewsets, permissions, status
from rest_framework.response import Response

from app.views import CustomPagination
from .models import NetworkProvider, AirtimePurchase
from .serializers import NetworkProviderSerializer, AirtimePurchaseSerializer
import requests
from django.conf import settings



class NetworkProviderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows network providers to be viewed.
    """
    queryset = NetworkProvider.objects.filter(active=True)
    serializer_class = NetworkProviderSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = CustomPagination


class AirtimePurchaseViewSet(viewsets.ModelViewSet):
    """
    API endpoint for creating and viewing Airtime purchases.
    """
    queryset = AirtimePurchase.objects.all()
    serializer_class = AirtimePurchaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        # Only return purchases for the logged-in user
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return AirtimePurchase.objects.all()
        return AirtimePurchase.objects.filter(user=user)

    def perform_create(self, serializer):
        # Ensure that logged-in user is associated with the purchase
        serializer.save(user=self.request.user)


    def create(self, request, *args, **kwargs):
        # Assign logged-in user to the new AirtimePurchase
        data = request.data.copy()
        data['user'] = request.user.pk

        # Get necessary fields from the request for the API
        phone_number = data.get('phone_number')
        amount = data.get('amount')
        network = data.get('network')  # Ensure your frontend passes provider code/identifier

        # Prepare payload for Maskawa API
        api_url = "https://maskawasubapi.com/api/v1/airtime/purchase"
        # You need to replace 'YOUR_API_KEY' with your actual API key from Maskawa
        api_key = settings.MASKAWA_API_KEY

        payload = {
            "network": network,
            "amount": str(amount),
            "phone": phone_number,
            # You might need to pass additional fields depending on Maskawa API requirements
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Call the Maskawa API
        try:
            api_response = requests.post(api_url, json=payload, headers=headers, timeout=15)
            api_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return Response(
                {"detail": "Airtime purchase failed: could not connect to provider", "error": str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # Parse the response from Maskawa API
        maskawa_resp = api_response.json()
        if not maskawa_resp.get("status") or maskawa_resp.get("status") != "success":
            return Response(
                {"detail": "Airtime purchase failed on provider", "response": maskawa_resp},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Proceed to save the AirtimePurchase
        # Optionally store the provider reference or transaction id
        provider_ref = maskawa_resp.get("data", {}).get("reference")

        # You can add any extra info from provider response to your serializer data before saving
        data['provider_reference'] = provider_ref

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers_out = self.get_success_headers(serializer.data)
        response_data = serializer.data
        response_data['maskawa_response'] = maskawa_resp  # Optionally include raw response

        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers_out)
