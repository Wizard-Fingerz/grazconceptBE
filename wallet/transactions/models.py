from django.db import models
from django.conf import settings
from wallet.models import Wallet
from wallet.saving_plans.models import SavingsPlan
# Do NOT import PaymentGateway here to avoid circular import issues

class WalletTransaction(models.Model):
    """
    Represents all wallet-related financial transactions.
    """
    TYPE_CHOICES = (
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('transfer', 'Transfer'),
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('savings_funding', 'Savings Funding'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='wallet_transactions', on_delete=models.CASCADE)
    wallet = models.ForeignKey(Wallet, related_name='transactions', on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    currency = models.CharField(max_length=10, default="NGN")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reference = models.CharField(max_length=128, unique=True)
    # Use a string reference to avoid circular import
    payment_gateway = models.ForeignKey(
        'PaymentGateway',
        related_name='transactions',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    meta = models.JSONField(blank=True, null=True, help_text="Flexible data for storing raw gateway responses, etc.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    savings_plan = models.ForeignKey(
        SavingsPlan, 
        related_name='transactions', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        help_text='If the transaction is related to a saving plan'
    )

    def __str__(self):
        return f"{self.transaction_type.title()} of {self.amount} {self.currency} by {self.user} ({self.status})"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['reference']),
        ]

