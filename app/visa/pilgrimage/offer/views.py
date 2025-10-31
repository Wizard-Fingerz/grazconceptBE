from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework import permissions
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
        destination = self.request.query_params.get('destination')
        pilgrimage_type = self.request.query_params.get('pilgrimage_type')
        is_active = self.request.query_params.get('is_active')
        limit = self.request.query_params.get('limit')

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
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        """
        Filters pilgrimage visa applications.
        If the user's user_type.term is "Customer", restrict to their own applications.
        Allows filtering by offer, applicant, and ?limit= query parameter for limiting results.
        """
        queryset = super().get_queryset()
        user = self.request.user

        # Check if the user is a Customer based on user_type.term
        is_customer = hasattr(user, 'user_type') and getattr(user.user_type, 'term', None) == 'Customer'
        if is_customer:
            client = getattr(user, 'client', None)
            if client:
                queryset = queryset.filter(applicant=client)
            else:
                # Defensive: No client object for this user, return empty queryset
                return queryset.none()

        offer_id = self.request.query_params.get('offer')
        applicant_id = self.request.query_params.get('applicant')
        limit = self.request.query_params.get('limit')

        # Only allow filtering by applicant if user is NOT a "Customer"
        if not is_customer and applicant_id:
            queryset = queryset.filter(applicant=applicant_id)
        if offer_id:
            queryset = queryset.filter(offer=offer_id)
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
        Always enforce applicant = current user's Client instance if user is a Customer.
        """
        user = request.user
        is_customer = hasattr(user, 'user_type') and getattr(user.user_type, 'term', None) == 'Customer'

        if is_customer and hasattr(user, 'client') and user.client:
            client = user.client
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(applicant=client)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            # Not a customer or no linked client, save as normal (applicant must be specified in payload)
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
