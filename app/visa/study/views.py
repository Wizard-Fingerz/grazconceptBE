from rest_framework import viewsets, permissions
from rest_framework.response import Response

from app.views import CustomPagination
from app.visa.study.serializers import StudyVisaApplicationSerializer
from .models import StudyVisaApplication
from rest_framework.permissions import IsAuthenticated


from rest_framework import status
from rest_framework.response import Response

class StudyVisaApplicationViewSet(viewsets.ModelViewSet):
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
                pass
        return queryset

    def list(self, request, *args, **kwargs):
        limit = request.query_params.get('limit')
        if limit is not None:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)   # applicant injected below
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        # Always enforce applicant = current user's Client instance
        from account.client.models import Client
        # print(self.request.user)
        client = Client.objects.get(pk=getattr(self.request.user, 'id', None))
        # print(client)
        serializer.save(applicant=client)
