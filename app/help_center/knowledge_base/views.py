from rest_framework import viewsets

from app.views import CustomPagination
from .models import FaqArticle
from .serializers import FaqArticleSerializer

class FaqArticleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows FAQ articles to be viewed or edited.
    """
    queryset = FaqArticle.objects.all()
    serializer_class = FaqArticleSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        """
        Optionally restricts returned FAQs to only active ones,
        by filtering against a 'is_active' query parameter in the URL.
        """
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset

