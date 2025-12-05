from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework import permissions
from app.views import CustomPagination
from .models import PilgrimageOffer, PilgrimageVisaApplication, PilgrimageVisaApplicationComment
from .serializers import (
    PilgrimageOfferSerializer,
    PilgrimageVisaApplicationSerializer,
    PilgrimageVisaApplicationCommentSerializer,
)
from rest_framework.decorators import action
from django.db.models import Q
from django.core.exceptions import FieldError

class PilgrimageOfferViewSet(viewsets.ModelViewSet):
    queryset = PilgrimageOffer.objects.all()
    serializer_class = PilgrimageOfferSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination

    def get_queryset(self):
        """
        Optionally restricts the returned pilgrimage offers by filtering against
        query parameters in the URL. Supports filtering by destination, pilgrimage_type,
        sponsorship, city, is_active, price range, created_at date range. Also supports
        free-text search (search), and ?limit= query param for limiting results.
        """
        queryset = super().get_queryset()
        params = self.request.query_params

        destination = params.get('destination')
        pilgrimage_type = params.get('pilgrimage_type')
        sponsorship = params.get('sponsorship')
        city = params.get('city')
        is_active = params.get('is_active')
        min_price = params.get('min_price')
        max_price = params.get('max_price')
        search_term = params.get('search')
        limit = params.get('limit')
        start_date = params.get('start_date')
        end_date = params.get('end_date')

        if destination:
            queryset = queryset.filter(destination__iexact=destination)
        if pilgrimage_type:
            try:
                pilgrimage_type_pk = int(pilgrimage_type)
                queryset = queryset.filter(pilgrimage_type__pk=pilgrimage_type_pk)
            except (ValueError, TypeError):
                queryset = queryset.filter(pilgrimage_type__term__icontains=pilgrimage_type)
        if sponsorship:
            try:
                sponsorship_pk = int(sponsorship)
                queryset = queryset.filter(sponsorship__pk=sponsorship_pk)
            except (ValueError, TypeError):
                queryset = queryset.filter(sponsorship__term__icontains=sponsorship)
        if city:
            queryset = queryset.filter(city__icontains=city)
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
            search_q |= Q(city__icontains=search_term)
            search_q |= Q(pilgrimage_type__term__icontains=search_term)
            search_q |= Q(sponsorship__term__icontains=search_term)
            search_q |= Q(sponsor_name__icontains=search_term)
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

class PilgrimageVisaApplicationViewSet(viewsets.ModelViewSet):
    queryset = PilgrimageVisaApplication.objects.all()
    serializer_class = PilgrimageVisaApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        """
        Filters pilgrimage visa applications.
        If the user's user_type.term is "Customer", restrict to their own applications.
        Allows filtering by offer, applicant, application status, search, and limit.
        """
        queryset = super().get_queryset()
        params = self.request.query_params
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

        offer_id = params.get('offer')
        applicant_id = params.get('applicant')
        status_param = params.get('status')
        search_term = params.get('search')
        limit = params.get('limit')
        created_after = params.get('created_after')
        created_before = params.get('created_before')

        # Only allow filtering by applicant if user is NOT a "Customer"
        if not is_customer and applicant_id:
            queryset = queryset.filter(applicant=applicant_id)
        if offer_id:
            queryset = queryset.filter(offer=offer_id)
        if status_param:
            try:
                queryset = queryset.filter(status__pk=int(status_param))
            except (ValueError, TypeError):
                queryset = queryset.filter(status__term__icontains=status_param)
        if created_after:
            queryset = queryset.filter(created_at__gte=created_after)
        if created_before:
            queryset = queryset.filter(created_at__lte=created_before)
        if search_term:
            search_q = Q()
            search_q |= Q(offer__title__icontains=search_term)
            search_q |= Q(applicant__user__full_name__icontains=search_term)
            search_q |= Q(applicant__user__username__icontains=search_term)
            search_q |= Q(status__term__icontains=search_term)
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

class PilgrimageVisaApplicationCommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for CRUD operations on PilgrimageVisaApplicationComment.
    Auto-assigns applicant/admin sender roles based on the current user.
    """
    queryset = PilgrimageVisaApplicationComment.objects.all()
    serializer_class = PilgrimageVisaApplicationCommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination

    def get_queryset(self):
        """
        Optionally filters by visa_application, applicant, admin, search, and read flags.
        Customers only see their own comments.
        """
        queryset = super().get_queryset()
        params = self.request.query_params
        user = self.request.user

        # Only let "Customer" users see their own comments
        is_customer = hasattr(user, 'user_type') and getattr(user.user_type, 'term', None) == 'Customer'
        if is_customer and hasattr(user, 'client'):
            queryset = queryset.filter(applicant=user.client)

        visa_application = params.get('visa_application')
        applicant = params.get('applicant')
        admin = params.get('admin')
        is_read_by_applicant = params.get('is_read_by_applicant')
        is_read_by_admin = params.get('is_read_by_admin')
        search = params.get('search')
        limit = params.get('limit')

        if visa_application:
            queryset = queryset.filter(visa_application=visa_application)
        if applicant:
            queryset = queryset.filter(applicant=applicant)
        if admin:
            queryset = queryset.filter(admin=admin)
        if is_read_by_applicant is not None:
            val = str(is_read_by_applicant).strip().lower()
            if val in {'true', '1', 'yes', 'on'}:
                queryset = queryset.filter(is_read_by_applicant=True)
            elif val in {'false', '0', 'no', 'off'}:
                queryset = queryset.filter(is_read_by_applicant=False)
        if is_read_by_admin is not None:
            val = str(is_read_by_admin).strip().lower()
            if val in {'true', '1', 'yes', 'on'}:
                queryset = queryset.filter(is_read_by_admin=True)
            elif val in {'false', '0', 'no', 'off'}:
                queryset = queryset.filter(is_read_by_admin=False)
        if search:
            q = Q()
            q |= Q(text__icontains=search)
            q |= Q(applicant__user__full_name__icontains=search)
            q |= Q(applicant__user__username__icontains=search)
            q |= Q(admin__username__icontains=search)
            try:
                queryset = queryset.filter(q)
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

    def perform_create(self, serializer):
        """
        Automatically set applicant or admin fields based on current user.
        """
        user = self.request.user
        if hasattr(user, 'user_type') and getattr(user.user_type, 'term', None) == 'Customer' and hasattr(user, 'client'):
            serializer.save(applicant=user.client, admin=None)
        elif hasattr(user, 'is_staff') and user.is_staff:
            serializer.save(admin=user, applicant=None)
        else:
            # Default: save as is (fallback for unexpected user types)
            serializer.save()


    @action(
        detail=False,
        methods=['get'],
        url_path='(?P<visa_application_id>[^/.]+)/comments',
        url_name='pilgrimage-visa-application-comments-by-visa-id'  # for clarity, matches new DRF naming
    )
    def list_by_application(self, request, visa_application_id=None):
        """
        Custom route for: /api/app/pilgrimage-visa-application/<visa_application_id>/comments/
        (See @file_context_0 for router context: the main comment viewset is at /api/app/pilgrimage-visa-application-comments/)
        """
        # Set on view kwargs for get_queryset()
        self.kwargs['visa_application_id'] = visa_application_id
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['post'],
        url_path='(?P<visa_application_id>[^/.]+)/create',
        url_name='pilgrimage-visa-application-comments-create'  # for clarity
    )
    def create_by_application(self, request, visa_application_id=None):
        """
        Custom route for posting a comment to: /api/app/pilgrimage-visa-application/<visa_application_id>/comments/
        The default viewset action will use: /api/app/pilgrimage-visa-application-comments/
        """
        data = request.data.copy()
        data['visa_application'] = visa_application_id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

