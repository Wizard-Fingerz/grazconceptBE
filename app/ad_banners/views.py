from rest_framework import viewsets, permissions
from rest_framework.permissions import IsAuthenticated
from app.views import CustomPagination
from .models import AdBanner
from .serializers import AdBannerSerializer
from rest_framework.response import Response


class AdBannerViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing AdBanner instances.
    """
    queryset = AdBanner.objects.all().order_by('-created_at')
    serializer_class = AdBannerSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination


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

