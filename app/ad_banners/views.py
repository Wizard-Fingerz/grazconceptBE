from rest_framework import viewsets, permissions
from rest_framework.permissions import IsAuthenticated
from app.views import CustomPagination
from .models import AdBanner
from .serializers import AdBannerSerializer


class AdBannerViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing AdBanner instances.
    Supports limiting results via ?limit=3 (returns most recent N banners, disables pagination).
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

    # Remove custom list() override to always use paginated response
