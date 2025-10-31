from rest_framework import viewsets
from rest_framework.response import Response
from app.views import CustomPagination
from app.visa.study.serializers import StudyVisaApplicationSerializer
from .models import StudyVisaApplication
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

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
