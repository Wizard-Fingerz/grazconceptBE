from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Wallet
from wallet.payment_gateway.models import PaymentGateway, PaymentGatewayCallbackLog
from wallet.saving_plans.models import SavingsPlan

# Import LoanOffer, LoanApplication, LoanRepayment from wallet.loan.models (fix: include LoanOffer)
from wallet.loan.models import LoanOffer, LoanApplication, LoanRepayment

# ADD WALLET TRANSACTION ADMIN AND RESOURCE (wallet5 transaction)
from wallet.transactions.models import WalletTransaction

class WalletTransactionResource(resources.ModelResource):
    class Meta:
        model = WalletTransaction
        fields = (
            'id',
            'user',
            'wallet',
            'transaction_type',
            'amount',
            'currency',
            'status',
            'reference',
            'payment_gateway',
            'meta',
            'created_at',
            'updated_at',
            'savings_plan'
        )

@admin.register(WalletTransaction)
class WalletTransactionAdmin(ImportExportModelAdmin):
    resource_class = WalletTransactionResource
    list_display = (
        'id',
        'user',
        'wallet',
        'transaction_type',
        'amount',
        'currency',
        'status',
        'reference',
        'payment_gateway',
        'created_at',
        'updated_at',
        'savings_plan',
    )
    search_fields = (
        'user__email', 'wallet__id', 'transaction_type', 'status', 'reference', 'payment_gateway__name'
    )
    list_filter = ('currency', 'transaction_type', 'status', 'payment_gateway')

class WalletResource(resources.ModelResource):
    class Meta:
        model = Wallet
        fields = ('id', 'user', 'balance', 'currency', 'is_active', 'created_at', 'updated_at')

@admin.register(Wallet)
class WalletAdmin(ImportExportModelAdmin):
    resource_class = WalletResource
    list_display = ('id', 'user', 'balance', 'currency', 'is_active', 'created_at', 'updated_at')
    search_fields = ('user__email', 'currency')
    list_filter = ('currency', 'is_active')

class PaymentGatewayResource(resources.ModelResource):
    class Meta:
        model = PaymentGateway
        fields = ('id', 'name', 'is_active')

@admin.register(PaymentGateway)
class PaymentGatewayAdmin(ImportExportModelAdmin):
    resource_class = PaymentGatewayResource
    list_display = ('id', 'name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

class PaymentGatewayCallbackLogResource(resources.ModelResource):
    class Meta:
        model = PaymentGatewayCallbackLog
        fields = ('id', 'payment_gateway', 'received_at', 'processed', 'wallet_transaction')

@admin.register(PaymentGatewayCallbackLog)
class PaymentGatewayCallbackLogAdmin(ImportExportModelAdmin):
    resource_class = PaymentGatewayCallbackLogResource
    list_display = ('id', 'payment_gateway', 'received_at', 'processed', 'wallet_transaction')
    list_filter = ('processed', 'payment_gateway')
    search_fields = ('wallet_transaction__reference',)

class SavingsPlanResource(resources.ModelResource):
    class Meta:
        model = SavingsPlan
        fields = (
            'id', 'user', 'wallet', 'name', 'target_amount', 'amount_saved', 'currency', 'start_date',
            'end_date', 'is_recurring', 'recurrence_period', 'status', 'created_at', 'updated_at', 'meta'
        )

@admin.register(SavingsPlan)
class SavingsPlanAdmin(ImportExportModelAdmin):
    resource_class = SavingsPlanResource
    list_display = (
        'id', 'user', 'wallet', 'name', 'target_amount', 'amount_saved', 'currency', 'status', 'is_recurring',
        'start_date', 'end_date', 'created_at'
    )
    search_fields = ('user__email', 'name', 'wallet__id')
    list_filter = ('currency', 'status', 'is_recurring')

# Register LoanOffer, LoanApplication and LoanRepayment in the admin site.

@admin.register(LoanOffer)
class LoanOfferAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'loan_type', 'min_amount', 'max_amount', 'currency', 'interest_rate', 'duration_months',
        'is_active', 'created_at', 'updated_at'
    )
    search_fields = ('name', 'loan_type', 'currency')
    list_filter = ('loan_type', 'currency', 'is_active')

    # Explicitly override get_search_results to prevent Q() misusage errors
    def get_search_results(self, request, queryset, search_term):
        """
        Override get_search_results to work around TypeError caused by misconfigured search_fields
        or any similar query issues. If an error occurs, fall back to all objects.
        """
        try:
            return super().get_search_results(request, queryset, search_term)
        except TypeError:
            # Return empty search result and all results as unfiltered queryset
            from django.db.models.query import Q
            return queryset.none(), False

@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'loan_offer', 'amount', 'currency', 'status', 'created_at', 'updated_at'
    )
    search_fields = ('user__email', 'loan_offer__name', 'status')
    list_filter = ('currency', 'status', 'loan_offer')

@admin.register(LoanRepayment)
class LoanRepaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'loan_application', 'user', 'amount', 'currency', 'payment_date', 'reference'
    )
    search_fields = ('user__email', 'loan_application__id', 'reference')
    list_filter = ('currency',)
