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
        is_customer = hasattr(user, 'user_type') and getattr(user.user_type, 'term', None) == 'Customer'
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
        is_customer = hasattr(user, 'user_type') and getattr(user.user_type, 'term', None) == 'Customer'
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
            admin = user if user.is_staff or hasattr(user, "is_admin") else None
        serializer.save(applicant=applicant, admin=admin)

    @action(
        detail=False,
        methods=['get'],
        url_path='(?P<visa_application_id>[^/.]+)/comments',
        url_name='study-visa-application-comments-by-visa-id'  # for clarity, matches new DRF naming
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

