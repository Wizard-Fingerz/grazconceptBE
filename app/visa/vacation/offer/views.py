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

from django.db.models import Q
from django.core.exceptions import FieldError

class VacationOfferViewSet(viewsets.ModelViewSet):
    queryset = VacationOffer.objects.all()
    serializer_class = VacationOfferSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination

    def get_queryset(self):
        """
        Optionally restricts the returned VacationOffers by filtering against
        query parameters in the URL. Supports filtering by destination, hotel_stars,
        is_active, price (min_price, max_price), date range (start_date, end_date), and search.
        Also supports 'limit' param for limiting results like pilgrimage's viewset.
        """
        queryset = super().get_queryset()
        params = self.request.query_params

        destination = params.get('destination')
        hotel_stars = params.get('hotel_stars')
        is_active = params.get('is_active')
        min_price = params.get('min_price')
        max_price = params.get('max_price')
        search_term = params.get('search')
        limit = params.get('limit')
        start_date = params.get('start_date')
        end_date = params.get('end_date')

        if destination:
            queryset = queryset.filter(destination__iexact=destination)
        if hotel_stars:
            try:
                queryset = queryset.filter(hotel_stars=int(hotel_stars))
            except (ValueError, TypeError):
                queryset = queryset.filter(hotel_stars=hotel_stars)
        if is_active is not None:
            true_values = {'true', '1', 'yes', 'on'}
            false_values = {'false', '0', 'no', 'off'}
            is_active_val = str(is_active).strip().lower()
            if is_active_val in true_values:
                queryset = queryset.filter(is_active=True)
            elif is_active_val in false_values:
                queryset = queryset.filter(is_active=False)
        if min_price:
            try:
                queryset = queryset.filter(price__gte=float(min_price))
            except (ValueError, TypeError):
                pass
        if max_price:
            try:
                queryset = queryset.filter(price__lte=float(max_price))
            except (ValueError, TypeError):
                pass
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)
        # Full-text or partial search across multiple fields
        if search_term:
            search_q = Q()
            search_q |= Q(title__icontains=search_term)
            search_q |= Q(description__icontains=search_term)
            search_q |= Q(destination__icontains=search_term)
            search_q |= Q(hotel_stars__icontains=search_term)
            # Add other relevant fields if needed
            try:
                queryset = queryset.filter(search_q)
            except FieldError:
                pass

        if limit is not None:
            try:
                limit_value = int(limit)
                if limit_value > 0:
                    return queryset[:limit_value]
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

    def create(self, request, *args, **kwargs):
        user = request.user
        # Determine applicant based on user type
        data = request.data.copy()
        if hasattr(user, 'user_type') and getattr(user.user_type, 'term', '').lower() == 'customer' \
            and hasattr(user, "client") and user.client:
            data['applicant'] = user.client.id
        elif hasattr(user, "client") and user.client:
            data['applicant'] = user.client.id  # Default: set to user.client if available
        # else, allow posted applicant

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
