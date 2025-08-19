from django.urls import path
from .views import SignUpView, UserProfileView, MyTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('users/register/', SignUpView.as_view(), name='register'),
    path('users/profile/', UserProfileView.as_view(), name='profile'),
    path('users/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('users/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
