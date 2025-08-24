from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ClientDocuments
from .serializers import ClientDocumentsSerializer

class ClientDocumentsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows client documents to be viewed or edited.
    """
    queryset = ClientDocuments.objects.all().order_by("-uploaded_at")
    serializer_class = ClientDocumentsSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
