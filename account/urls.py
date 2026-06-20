from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from account.client.documents.views import ClientDocumentsViewSet
from account.client.views import ClientViewSet
from .views import (
    AdminUserAnalyticsView,
    SignUpView,
    UserProfileView,
    UserProfileUpdateView,
    CustomerDashboardView,
    MyTokenObtainPairView,
    UserViewSet,
    GetMyRefeereesView,
    AdminDashboardAnalyticsView,
    AdminAnalyticsReportView,
)

router = DefaultRouter()
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'clients-document', ClientDocumentsViewSet, basename='client_documents')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # Auth
    path('users/register/', SignUpView.as_view(), name='register'),
    path('users/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('users/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Profile  (GET + PATCH profile_picture)
    path('users/profile/', UserProfileView.as_view(), name='profile'),
    # PATCH all profile + extended fields (JSON body)
    path('users/profile/update/', UserProfileUpdateView.as_view(), name='profile_update'),

    # Customer dashboard stats
    path('users/dashboard/', CustomerDashboardView.as_view(), name='customer_dashboard'),

    # Referrals
    path('users/my-referees/', GetMyRefeereesView.as_view(), name='my_referees'),

    # Admin analytics
    path('admin/dashboard-analytics/', AdminDashboardAnalyticsView.as_view(), name='admin_dashboard_analytics'),
    path('admin/analytics-report/', AdminAnalyticsReportView.as_view(), name='admin_analytics_report'),
    path('admin/user-analytics/', AdminUserAnalyticsView.as_view(), name='admin_user_analytics'),

    # ViewSet routes
    path('', include(router.urls)),
]
