from rest_framework import viewsets
from .models import (
    VacationOffer,
    VacationOfferIncludedItem,
    VacationOfferImage,
    VacationVisaApplication,
)
from .serializers import (
    VacationOfferSerializer,
    VacationOfferIncludedItemSerializer,
    VacationOfferImageSerializer,
    VacationVisaApplicationSerializer,
)
from rest_framework import permissions
from app.views import CustomPagination


class VacationOfferViewSet(viewsets.ModelViewSet):
    queryset = VacationOffer.objects.all()
    serializer_class = VacationOfferSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination

    def get_queryset(self):
        """
        Optionally restricts the returned offers by filtering against
        query parameters in the URL. Supports 'limit' param for limiting results.
        """
        queryset = super().get_queryset()
        destination = self.request.query_params.get('destination')
        is_active = self.request.query_params.get('is_active')
        limit = self.request.query_params.get('limit')

        if destination:
            queryset = queryset.filter(destination=destination)
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


class VacationOfferIncludedItemViewSet(viewsets.ModelViewSet):
    queryset = VacationOfferIncludedItem.objects.all()
    serializer_class = VacationOfferIncludedItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination

class VacationOfferImageViewSet(viewsets.ModelViewSet):
    queryset = VacationOfferImage.objects.all()
    serializer_class = VacationOfferImageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination

class VacationVisaApplicationViewSet(viewsets.ModelViewSet):
    queryset = VacationVisaApplication.objects.all()
    serializer_class = VacationVisaApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        """
        Filters vacation visa applications.
        If the user is a client (user.role.term == "client"), restrict to their own applications.
        Allows filtering by offer, applicant, and status.
        """
        queryset = super().get_queryset()
        offer = self.request.query_params.get('offer')
        applicant = self.request.query_params.get('applicant')
        status = self.request.query_params.get('status')

        user = self.request.user

        # Check if the user is a client based on role.term
        is_client = hasattr(user, 'role') and getattr(user.role, 'term', None) == 'client'
        if is_client:
            # If user is client, restrict to their own applications
            client = getattr(user, 'client', None)
            if client:
                queryset = queryset.filter(applicant=client)
            else:
                # Defensive: No client object for this user, return empty queryset
                return queryset.none()
        else:
            # Only allow general filtering by applicant if user is not a client
            if applicant:
                queryset = queryset.filter(applicant_id=applicant)

        if offer:
            queryset = queryset.filter(offer_id=offer)
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        is_client = hasattr(user, 'role') and getattr(user.role, 'term', None) == 'client'
        if is_client and hasattr(user, "client") and user.client:
            serializer.save(applicant=user.client)
        else:
            serializer.save()

