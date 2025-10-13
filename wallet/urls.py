from rest_framework import routers
from .views import WalletViewSet
from .transactions.views import WalletTransactionViewSet

router = routers.DefaultRouter()
router.register(r'wallets', WalletViewSet, basename='wallet')
router.register(r'wallet-transactions', WalletTransactionViewSet, basename='wallet-transaction')

urlpatterns = router.urls
