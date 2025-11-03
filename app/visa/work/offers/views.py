from rest_framework import viewsets
from rest_framework import permissions
from app.views import CustomPagination
from app.visa.work.offers.models import CVSubmission, WorkVisaOffer, WorkVisaApplication, WorkVisaInterview
from app.visa.work.offers.serializers import (
    CVSubmissionSerializer,
    WorkVisaOfferSerializer,
    WorkVisaApplicationSerializer,
    # InterviewFAQSerializer,
    WorkVisaInterviewSerializer,
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


# class InterviewFAQViewSet(viewsets.ModelViewSet):
#     queryset = InterviewFAQ.objects.all()
#     serializer_class = InterviewFAQSerializer
#     permission_classes = [permissions.IsAuthenticatedOrReadOnly]
#     pagination_class = CustomPagination


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

