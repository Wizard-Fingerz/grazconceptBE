from rest_framework.views import APIView
from django.db import models
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import viewsets
from rest_framework.response import Response
from app.views import CustomPagination
from app.visa.study.serializers import StudyVisaApplicationCommentSerializer, StudyVisaApplicationSerializer
from .models import StudyVisaApplication, StudyVisaApplicationComment
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.decorators import action


class StudyVisaApplicationViewSet(viewsets.ModelViewSet):
    queryset = StudyVisaApplication.objects.all().order_by('-application_date')
    serializer_class = StudyVisaApplicationSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filters study visa applications.
        If the user's user_type.term is "Customer", restrict to their own applications.
        Allows filtering by ?limit= query parameter for limiting results.
        """
        queryset = super().get_queryset()
        user = self.request.user

        # Check if the user is a Customer based on user_type.term
        is_customer = hasattr(user, 'user_type') and getattr(
            user.user_type, 'term', None) == 'Customer'
        if is_customer:
            client = getattr(user, 'client', None)
            if client:
                queryset = queryset.filter(applicant=client)
            else:
                # Defensive: No client object for this user, return empty queryset
                return queryset.none()

        limit = self.request.query_params.get('limit')
        if limit is not None:
            try:
                limit = int(limit)
                if limit > 0:
                    queryset = queryset[:limit]
            except (ValueError, TypeError):
                pass
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        # Always enforce applicant = current user's Client instance
        user = self.request.user
        is_customer = hasattr(user, 'user_type') and getattr(
            user.user_type, 'term', None) == 'Customer'
        if is_customer and hasattr(user, "client") and user.client:
            serializer.save(applicant=user.client)
        else:
            serializer.save()


class StudyVisaApplicationCommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling comments on Study Visa Applications.
    Allows list/create for /api/app/study-visa-application-comments/ or via application-specific route
    """
    queryset = StudyVisaApplicationComment.objects.all()
    serializer_class = StudyVisaApplicationCommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination

    def get_queryset(self):
        """
        Optionally filter comments by ?visa_application=<id> or by nested URL /study-visa-application/<id>/comments/
        """
        queryset = super().get_queryset()
        # Support both nested route and query param for filtering, or router path
        visa_application_id = (
            self.kwargs.get('visa_application_id')
            or self.request.query_params.get('visa_application')
        )
        if visa_application_id:
            queryset = queryset.filter(visa_application_id=visa_application_id)
        return queryset

    def perform_create(self, serializer):
        """
        Sets the sender fields based on the user
        """
        user = self.request.user
        applicant = getattr(user, 'applicant', None)
        admin = None
        if not applicant:
            admin = user if user.is_staff or hasattr(
                user, "is_admin") else None
        serializer.save(applicant=applicant, admin=admin)

    @action(
        detail=False,
        methods=['get'],
        url_path='(?P<visa_application_id>[^/.]+)/comments',
        # for clarity, matches new DRF naming
        url_name='study-visa-application-comments-by-visa-id'
    )
    def list_by_application(self, request, visa_application_id=None):
        """
        Custom route for: /api/app/study-visa-application/<visa_application_id>/comments/
        (See @file_context_0 for router context: the main comment viewset is at /api/app/study-visa-application-comments/)
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
        url_name='study-visa-application-comments-create'  # for clarity
    )
    def create_by_application(self, request, visa_application_id=None):
        """
        Custom route for posting a comment to: /api/app/study-visa-application/<visa_application_id>/comments/
        The default viewset action will use: /api/app/study-visa-application-comments/
        """
        data = request.data.copy()
        data['visa_application'] = visa_application_id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        # Admin Analytics APIView for Study Visa Applications


class StudyVisaApplicationAnalyticsView(APIView):
    """
    Admin analytics for Study Visa Applications.

    - Counts by status (all statuses in study_visa_status TableDropDownDefinition)
    - By institution
    - By destination_country

    Optional filters (as query params):
        - institution (institution id)
        - country (destination country code/string)
        - start_date, end_date (application_date)
    """

    def get(self, request):
        from app.visa.study.models import StudyVisaApplication
        from definition.models import TableDropDownDefinition
        from django.db.models import Count

        # Only staff or admin users allowed
        if not (request.user.is_staff or getattr(request.user, 'is_admin', False)):
            return Response({"detail": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)

        institution_id = request.query_params.get('institution')
        country = request.query_params.get('country')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        qs = StudyVisaApplication.objects.all()

        if institution_id:
            qs = qs.filter(institution_id=institution_id)
        if country:
            # Check both institution.country and study_visa_offer institution country
            qs = qs.filter(
                models.Q(institution__country=country) |
                models.Q(study_visa_offer__institution__country=country)
            )
        if start_date:
            qs = qs.filter(application_date__gte=start_date)
        if end_date:
            qs = qs.filter(application_date__lte=end_date)

        # Get all statuses in system defined order
        all_status_terms = [
            "Draft",
            "Completed",
            "Approved",
            "Rejected",
            "Received Application",
            "Pending From Student",
            "Application Submitted to the Institution",
            "Application on hold, Intake not yet open",
            "Case Closed",
            "Rejected By the institution",
            "Conditional offer Received",
            "Unconditional Offer received",
            "Payment Received",
            "Visa  granted ",
            "Visa Denied"
        ]

        # Look up all status TableDropDownDefinitions (for possible mapping, not strictly needed)
        status_qs = TableDropDownDefinition.objects.filter(
            table_name="study_visa_status",
            term__in=[s.strip() for s in all_status_terms]
        )
        status_term_map = {s.term.strip(): s.id for s in status_qs}

        # Do a count-group-by-status FK (NULL ⇒ "Unknown")
        status_counts = (
            qs.values("status__term")
              .annotate(count=Count("id"))
        )
        by_status = {s: 0 for s in all_status_terms}
        for row in status_counts:
            key = row["status__term"] or "Unknown"
            # Sometimes admins enter ad-hoc status not in list
            if key in by_status:
                by_status[key] = row["count"]
            else:
                by_status.setdefault(key, 0)
                by_status[key] += row["count"]

        total = qs.count()

        # By institution
        inst_counts = (
            qs.values("institution__name")
              .annotate(count=Count("id"))
              .order_by("-count")
        )
        by_institution = {row["institution__name"]
                          or "No institution": row["count"] for row in inst_counts}

        # By destination country -- using model property for reliability
        country_counts = {}
        for app in qs:
            dest_country = app.destination_country
            key = str(dest_country) if dest_country else "Unknown"
            country_counts[key] = country_counts.get(key, 0) + 1

        return Response({
            "total": total,
            "by_status": by_status,
            "by_institution": by_institution,
            "by_country": country_counts,
        })
