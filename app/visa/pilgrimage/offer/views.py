from rest_framework import viewsets, status
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from app.views import CustomPagination
from .models import PilgrimageOffer, PilgrimageVisaApplication
from .serializers import PilgrimageOfferSerializer, PilgrimageVisaApplicationSerializer

class PilgrimageOfferViewSet(viewsets.ModelViewSet):
    queryset = PilgrimageOffer.objects.all()
    serializer_class = PilgrimageOfferSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination

    def get_queryset(self):
        """
        Optionally restricts the returned offers by filtering against
        query parameters in the URL. Supports 'limit' param for limiting results.
        """
        queryset = super().get_queryset()
        destination = self.request.query_params.get("destination")
        pilgrimage_type = self.request.query_params.get("pilgrimage_type")
        is_active = self.request.query_params.get("is_active")
        limit = self.request.query_params.get("limit")

        if destination:
            queryset = queryset.filter(destination=destination)
        if pilgrimage_type:
            queryset = queryset.filter(pilgrimage_type=pilgrimage_type)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() in ['true', '1'])
        if limit is not None:
            try:
                limit_value = int(limit)
                if limit_value > 0:
                    queryset = queryset[:limit_value]
            except (ValueError, TypeError):
                pass  # Ignore invalid limit values
        return queryset

class PilgrimageVisaApplicationViewSet(viewsets.ModelViewSet):
    queryset = PilgrimageVisaApplication.objects.all()
    serializer_class = PilgrimageVisaApplicationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        offer_id = self.request.query_params.get("offer")
        applicant_id = self.request.query_params.get("applicant")
        limit = self.request.query_params.get("limit")

        if offer_id:
            queryset = queryset.filter(offer=offer_id)
        if applicant_id:
            queryset = queryset.filter(applicant=applicant_id)
        if limit is not None:
            try:
                limit_value = int(limit)
                if limit_value > 0:
                    queryset = queryset[:limit_value]
            except (ValueError, TypeError):
                pass
        return queryset

    def create(self, request, *args, **kwargs):
        """
        Ensure that the applicant is injected from the authenticated user.
        If the user is not authenticated as a client, raise the required error in the correct format.
        """
        data = request.data.copy()
        from account.client.models import Client

        # Ensure the user is authenticated and mapped to a Client
        client_id = getattr(request.user, 'id', None)
        if not client_id:
            raise ValidationError({'applicant': ['This field is required.']})

        try:
            client = Client.objects.get(user_ptr=client_id)
        except Client.DoesNotExist:
            raise ValidationError({'applicant': ['This field is required.']})
        data['applicant'] = client.id  # Inject applicant into request data

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(applicant=client)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
