from rest_framework import viewsets, permissions
from rest_framework.response import Response

from app.views import CustomPagination
from app.visa.study.serializers import StudyVisaApplicationSerializer
from .models import StudyVisaApplication
from rest_framework.permissions import IsAuthenticated


class StudyVisaApplicationViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing study visa application instances.
    Supports limiting results via ?limit=3 (returns most recent N applications, disables pagination).
    """
    queryset = StudyVisaApplication.objects.all().order_by('-application_date')
    serializer_class = StudyVisaApplicationSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        limit = self.request.query_params.get('limit')
        if limit is not None:
            try:
                limit = int(limit)
                if limit > 0:
                    return queryset[:limit]
            except (ValueError, TypeError):
                pass  # Ignore invalid limit, fallback to default queryset
        return queryset

    def list(self, request, *args, **kwargs):
        limit = request.query_params.get('limit')
        if limit is not None:
            # If limit is set, disable pagination and return only the limited results
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        # Otherwise, use default paginated response
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['applicant'] = request.user.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)
