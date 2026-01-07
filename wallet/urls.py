from rest_framework import routers
from django.urls import path, include
from .views import WalletViewSet, AdminWalletAnalyticsView
from .transactions.views import WalletTransactionViewSet
from .payment_gateway.views import PaymentGatewayViewSet, PaymentGatewayCallbackLogViewSet
from .saving_plans.views import SavingsPlanViewSet
from .loan.views import LoanOfferViewSet, LoanApplicationViewSet, LoanRepaymentViewSet, LoanAnalyticsViewSet

router = routers.DefaultRouter()
router.register(r'wallets', WalletViewSet, basename='wallet')
router.register(r'wallet-transactions', WalletTransactionViewSet, basename='wallet-transaction')
router.register(r'payment-gateways', PaymentGatewayViewSet, basename='payment-gateway')
router.register(r'payment-gateway-callback-logs', PaymentGatewayCallbackLogViewSet, basename='payment-gateway-callback-log')
router.register(r'saving-plans', SavingsPlanViewSet, basename='saving-plan')

router.register(r'loan-offers', LoanOfferViewSet, basename='loan-offer')
router.register(r'loan-applications', LoanApplicationViewSet, basename='loan-application')
router.register(r'loan-repayments', LoanRepaymentViewSet, basename='loan-repayment')
router.register(r'loan-analytics', LoanAnalyticsViewSet, basename='loan-analytics')

urlpatterns = [
    path('', include(router.urls)),
    path('admin-analytics/', AdminWalletAnalyticsView.as_view(), name='wallet-admin-analytics'),
]
