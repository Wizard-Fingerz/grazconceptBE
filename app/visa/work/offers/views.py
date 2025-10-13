from rest_framework import viewsets
from rest_framework import permissions
from app.views import CustomPagination
from app.visa.work.offers.models import WorkVisaOffer, WorkVisaApplication
from app.visa.work.offers.serializers import WorkVisaOfferSerializer, WorkVisaApplicationSerializer

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


    # Remove perform_create override, no longer needed since handled in create

