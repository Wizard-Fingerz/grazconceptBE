from rest_framework import viewsets, status
from rest_framework.response import Response
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
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from app.views import CustomPagination

from django.db.models import Q
from django.core.exceptions import FieldError


class VacationOfferViewSet(viewsets.ModelViewSet):
    queryset = VacationOffer.objects.all().order_by('-created_at')
    serializer_class = VacationOfferSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination

    def get_queryset(self):
        """
        Optionally filter VacationOffers by query params:
        destination, hotel_stars, is_active, min_price, max_price,
        date range, search, and supports limit.
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

        if search_term:
            search_q = (
                Q(title__icontains=search_term) |
                Q(description__icontains=search_term) |
                Q(destination__icontains=search_term)
            )
            # Do not try searching for hotel_stars if it's not a char field
            try:
                queryset = queryset.filter(search_q)
            except FieldError:
                pass

        if limit is not None:
            try:
                limit_value = int(limit)
                if limit_value > 0:
                    queryset = queryset[:limit_value]
            except (ValueError, TypeError):
                pass
        return queryset


class VacationOfferIncludedItemViewSet(viewsets.ModelViewSet):
    queryset = VacationOfferIncludedItem.objects.all()
    serializer_class = VacationOfferIncludedItemSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination


class VacationOfferImageViewSet(viewsets.ModelViewSet):
    queryset = VacationOfferImage.objects.all()
    serializer_class = VacationOfferImageSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination


class VacationVisaApplicationViewSet(viewsets.ModelViewSet):
    queryset = VacationVisaApplication.objects.all().order_by('-created_at')
    serializer_class = VacationVisaApplicationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        """
        If user is a customer, show only their vacation visa applications.
        Allows filtering by offer, applicant (if not customer), and status.
        """
        queryset = super().get_queryset()
        user = self.request.user

        offer = self.request.query_params.get('offer')
        applicant = self.request.query_params.get('applicant')
        status_val = self.request.query_params.get('status')

        is_customer = hasattr(user, 'user_type') and getattr(user.user_type, 'term', '').lower() == 'customer'
        client = getattr(user, 'client', None)

        if is_customer:
            if client:
                queryset = queryset.filter(applicant=client)
            else:
                return queryset.none()
        elif applicant:
            queryset = queryset.filter(applicant_id=applicant)

        if offer:
            queryset = queryset.filter(offer_id=offer)
        if status_val:
            queryset = queryset.filter(status=status_val)
        return queryset
    

    def create(self, request, *args, **kwargs):
        """
        Assign applicant id to the request data if user is a customer before saving.
        """
        user = request.user
        if hasattr(user, 'user_type') and getattr(user.user_type, 'term', '').lower() == 'customer' and hasattr(user, 'client') and user.client:
            if isinstance(request.data, dict):
                request.data['applicant'] = user.client.id
        return super().create(request, *args, **kwargs)

