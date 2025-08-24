from django.urls import path, include
from rest_framework.routers import DefaultRouter

from account.client.documents.views import ClientDocumentsViewSet
from .views import SignUpView, UserProfileView, MyTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView

from account.client.views import ClientViewSet

router = DefaultRouter()
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'clients-document', ClientDocumentsViewSet, basename='client_documents')


urlpatterns = [
    path('users/register/', SignUpView.as_view(), name='register'),
    path('users/profile/', UserProfileView.as_view(), name='profile'),
    path('users/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('users/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
]
