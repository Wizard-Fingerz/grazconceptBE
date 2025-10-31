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
        If the user's user_type.term is "Customer", restrict to their own applications only.
        Allows filtering by offer, applicant, and status for others.
        """
        queryset = super().get_queryset()
        offer = self.request.query_params.get('offer')
        applicant = self.request.query_params.get('applicant')
        status = self.request.query_params.get('status')

        user = self.request.user

        # Enforce: If the user.user_type.term is "Customer", return only their own applications
        if hasattr(user, 'user_type') and getattr(user.user_type, 'term', '').lower() == 'customer':
            client = getattr(user, 'client', None)
            if client:
                queryset = queryset.filter(applicant=client)
            else:
                # No client object for this user; return none.
                return queryset.none()
        else:
            # Only allow filtering by applicant if user is NOT a "Customer"
            if applicant:
                queryset = queryset.filter(applicant_id=applicant)

        if offer:
            queryset = queryset.filter(offer_id=offer)
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        # Always ensure applicant is set to user.client if user is a Customer
        if hasattr(user, 'user_type') and getattr(user.user_type, 'term', '').lower() == 'customer' \
            and hasattr(user, "client") and user.client:
            serializer.save(applicant=user.client)
        else:
            serializer.save()

