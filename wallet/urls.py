from rest_framework import routers
from .views import WalletViewSet
from .transactions.views import WalletTransactionViewSet
from .payment_gateway.views import PaymentGatewayViewSet, PaymentGatewayCallbackLogViewSet
from .saving_plans.views import SavingsPlanViewSet  # include saving plans

router = routers.DefaultRouter()
router.register(r'wallets', WalletViewSet, basename='wallet')
router.register(r'wallet-transactions', WalletTransactionViewSet, basename='wallet-transaction')
router.register(r'payment-gateways', PaymentGatewayViewSet, basename='payment-gateway')
router.register(r'payment-gateway-callback-logs', PaymentGatewayCallbackLogViewSet, basename='payment-gateway-callback-log')
router.register(r'saving-plans', SavingsPlanViewSet, basename='saving-plan')  # new route for saving plans

urlpatterns = router.urls
