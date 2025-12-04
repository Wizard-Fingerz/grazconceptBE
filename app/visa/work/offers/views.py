from rest_framework import viewsets
from rest_framework import permissions
from app.views import CustomPagination
from app.visa.work.offers.models import (
    CVSubmission,
    WorkVisaOffer,
    WorkVisaApplication,
    WorkVisaInterview,
    WorkVisaApplicationComment,
)
from app.visa.work.offers.serializers import (
    CVSubmissionSerializer,
    WorkVisaOfferSerializer,
    WorkVisaApplicationSerializer,
    WorkVisaInterviewSerializer,
    WorkVisaApplicationCommentSerializer,
)

from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework import status


class WorkVisaOfferViewSet(viewsets.ModelViewSet):
    queryset = WorkVisaOffer.objects.all()
    serializer_class = WorkVisaOfferSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination


class WorkVisaApplicationViewSet(viewsets.ModelViewSet):
    queryset = WorkVisaApplication.objects.all()
    serializer_class = WorkVisaApplicationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination

    def get_queryset(self):
        """
        Filters work visa applications.
        If the user's user_type.term is "Customer", restrict to their own applications only.
        Allows filtering by ?limit= query parameter for limiting results.
        """
        queryset = super().get_queryset()
        user = self.request.user

        # Enforce: If the user's user_type.term is "Customer", return only their own applications
        is_customer = hasattr(user, 'user_type') and getattr(user.user_type, 'term', None) == 'Customer'
        if is_customer:
            client = getattr(user, 'client', None)
            if client:
                queryset = queryset.filter(client=client)
            else:
                # No client object for this user; return none.
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
        """
        Ensure that the client is injected from the authenticated user.
        If the user is not authenticated as a client, raise the required error in the correct format.
        """
        data = request.data.copy()
        from account.client.models import Client

        # Ensure the user is authenticated and mapped to a Client
        client_id = getattr(request.user, 'id', None)
        if not client_id:
            # Matches the backend error format {"client":["This field is required."]}
            raise ValidationError({'client': ['This field is required.']})

        try:
            client = Client.objects.get(user_ptr=client_id)
        except Client.DoesNotExist:
            raise ValidationError({'client': ['This field is required.']})
        data['client'] = client.id  # Inject client into request data

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(client=client)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


from rest_framework.decorators import action
from rest_framework.response import Response

class WorkVisaApplicationCommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling comments on Work Visa Applications.
    Allows list/create for /api/app/work-visa-application-comments/ or via application-specific route
    """
    queryset = WorkVisaApplicationComment.objects.all()
    serializer_class = WorkVisaApplicationCommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination

    def get_queryset(self):
        """
        Optionally filter comments by ?visa_application=<id> or by nested URL /work-visa-application/<id>/comments/
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
        url_name='work-visa-application-comments'  # for clarity, matches new DRF naming
    )
    def list_by_application(self, request, visa_application_id=None):
        """
        Custom route for: /api/app/work-visa-application/<visa_application_id>/comments/
        (See @file_context_0 for router context: the main comment viewset is at /api/app/work-visa-application-comments/)
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
        url_path='(?P<visa_application_id>[^/.]+)/comments',
        url_name='work-visa-application-comments-create'  # for clarity
    )
    def create_by_application(self, request, visa_application_id=None):
        """
        Custom route for posting a comment to: /api/app/work-visa-application/<visa_application_id>/comments/
        The default viewset action will use: /api/app/work-visa-application-comments/
        """
        data = request.data.copy()
        data['visa_application'] = visa_application_id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class WorkVisaInterviewViewSet(viewsets.ModelViewSet):
    queryset = WorkVisaInterview.objects.all()
    serializer_class = WorkVisaInterviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination


class CVSubmissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing CV Submissions for work visa offers.
    """
    queryset = CVSubmission.objects.all()
    serializer_class = CVSubmissionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination

    def perform_create(self, serializer):
        # Optionally, link user or add additional logic here
        serializer.save()

    def get_queryset(self):
        """
        Optionally filter CV Submissions based on the current user or via query parameters.
        """
        queryset = super().get_queryset()
        job_id = self.request.query_params.get('job')
        if job_id:
            queryset = queryset.filter(job_id=job_id)
        return queryset

