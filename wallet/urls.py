from rest_framework import routers
from .views import WalletViewSet
from .transactions.views import WalletTransactionViewSet
from .payment_gateway.views import PaymentGatewayViewSet, PaymentGatewayCallbackLogViewSet
from .saving_plans.views import SavingsPlanViewSet  # include saving plans

# Import LoanApplicationViewSet, LoanRepaymentViewSet, and LoanAnalyticsViewSet from wallet.loan.views
from .loan.views import LoanApplicationViewSet, LoanRepaymentViewSet, LoanAnalyticsViewSet

router = routers.DefaultRouter()
router.register(r'wallets', WalletViewSet, basename='wallet')
router.register(r'wallet-transactions', WalletTransactionViewSet, basename='wallet-transaction')
router.register(r'payment-gateways', PaymentGatewayViewSet, basename='payment-gateway')
router.register(r'payment-gateway-callback-logs', PaymentGatewayCallbackLogViewSet, basename='payment-gateway-callback-log')
router.register(r'saving-plans', SavingsPlanViewSet, basename='saving-plan')  # new route for saving plans

# Register routes for loan application, loan repayment, and loan analytics
router.register(r'loan-applications', LoanApplicationViewSet, basename='loan-application')
router.register(r'loan-repayments', LoanRepaymentViewSet, basename='loan-repayment')
router.register(r'loan-analytics', LoanAnalyticsViewSet, basename='loan-analytics')

urlpatterns = router.urls
