from django.db import models

from wallet.transactions.models import WalletTransaction

# Corrected import string for WalletTransaction. 'wallet.transactions.WalletTransaction' is not a valid model reference.
# Use 'transactions.WalletTransaction' (app_label.ModelName, where app_label is the app name)

class PaymentGateway(models.Model):
    """
    Represents third-party payment gateways (e.g., Paystack, Flutterwave, Stripe).
    """
    GATEWAY_CHOICES = (
        ('paystack', 'Paystack'),
        ('flutterwave', 'Flutterwave'),
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('manual', 'Manual'),
    )
    name = models.CharField(max_length=50, choices=GATEWAY_CHOICES, unique=True)
    is_active = models.BooleanField(default=True)
    credentials = models.JSONField(blank=True, null=True, help_text="API keys, webhook secrets, etc.")

    def __str__(self):
        return self.get_name_display()


class PaymentGatewayCallbackLog(models.Model):
    """
    Logs all incoming callbacks/webhooks from payment gateways.
    """
    payment_gateway = models.ForeignKey(PaymentGateway, related_name='callback_logs', on_delete=models.CASCADE)
    payload = models.JSONField(help_text="Raw callback/webhook data")
    received_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    # Use correct app_label.ModelName for the ForeignKey relation
    wallet_transaction = models.ForeignKey(
        WalletTransaction,
        related_name='callback_logs',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    def __str__(self):
        return f"Callback {self.id} for {self.payment_gateway} at {self.received_at}"

