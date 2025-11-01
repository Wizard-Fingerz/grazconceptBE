from app.views import CustomPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

from .serializers import (
    PasswordResetRequestSerializer,
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
)
from .models import User
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny


class SignUpView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=UserRegistrationSerializer,
        responses={201: openapi.Response(
            'Created', UserRegistrationSerializer)},
    )
    def post(self, request):
        data = request.data.copy()

        
        serializer = UserRegistrationSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()

            # Generate JWT tokens for the new user
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)


            return Response(
                {
                    "user_id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "referred_by": user.referred_by,
                    "user_type": user.user_type.term if user.user_type else None,
                    "access": access_token,
                    "refresh": refresh_token,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token["email"] = user.email
        token["first_name"] = user.first_name
        token["user_type"] = user.user_type.term if user.user_type else None
        return token

    def validate(self, attrs):
        # Replace username with email for authentication
        attrs["username"] = attrs.get("email")
        return super().validate(attrs)


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class PasswordResetRequestView(APIView):
    @swagger_auto_schema(
        request_body=PasswordResetRequestSerializer, responses={
            200: openapi.Response("OK")}
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=email)
            token = default_token_generator.make_token(user)
            reset_url = f"{settings.FRONTEND_URL}/reset-password/{user.pk}/{token}/"
            send_mail(
                "Password Reset",
                f"Click the link to reset your password: {reset_url}",
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
        except UserModel.DoesNotExist:
            pass  # Don't reveal if email exists
        return Response(
            {"message": "If the email exists, a reset link has been sent."},
            status=status.HTTP_200_OK,
        )


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

        # GetMyRefeerees endpoint: returns all users referred by the authenticated user


from account.client.models import Client
from account.client.serializers import ClientSerializer

class GetMyRefeereesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # Get referees from User model (those whose 'referred_by' = this user's custom_id)
        user_referees = User.objects.filter(referred_by=user.custom_id)
        # Get referees from Client model (those whose 'referred_by' = this user's custom_id)
        client_referees = Client.objects.filter(referred_by=user.custom_id)

        # Combine both querysets as a list, tagging them for serialization
        combined = (
            [{'type': 'user', 'instance': u} for u in user_referees] +
            [{'type': 'client', 'instance': c} for c in client_referees]
        )

        # Sort combined by created_date descending, assuming both models have this field,
        # if not, fallback as-is
        try:
            combined.sort(key=lambda x: getattr(x['instance'], 'created_date', None), reverse=True)
        except Exception:
            pass

        paginator = CustomPagination()
        paginated_combined = paginator.paginate_queryset(combined, request)

        # Serialize keeping type info
        results = []
        for item in paginated_combined:
            if item['type'] == 'user':
                data = UserSerializer(item['instance']).data
                data['referee_type'] = 'user'
            else:
                data = ClientSerializer(item['instance']).data
                data['referee_type'] = 'client'
            results.append(data)

        return paginator.get_paginated_response(results)
