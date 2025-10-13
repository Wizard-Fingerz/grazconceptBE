from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Wallet
from wallet.payment_gateway.models import PaymentGateway, PaymentGatewayCallbackLog
from wallet.saving_plans.models import SavingsPlan  # include savig plan

class WalletResource(resources.ModelResource):
    class Meta:
        model = Wallet
        fields = ('id', 'user', 'balance', 'currency', 'is_active', 'created_at', 'updated_at')

@admin.register(Wallet)
class WalletAdmin(ImportExportModelAdmin):
    resource_class = WalletResource
    list_display = ('id', 'user', 'balance', 'currency', 'is_active', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'currency')
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

# Include SavingsPlan in admin
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
    search_fields = ('user__username', 'user__email', 'name', 'wallet__id')
    list_filter = ('currency', 'status', 'is_recurring')
