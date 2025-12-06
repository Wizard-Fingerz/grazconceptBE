from django.db import models
from django.conf import settings

class NetworkProvider(models.Model):
    """
    Model representing a mobile network provider for airtime services.
    """
    value = models.CharField(
        max_length=20, 
        unique=True, 
        help_text="Short code or identifier, e.g., 'mtn', 'airtel', 'glo', '9mobile'",
        db_index=True,
    )
    label = models.CharField(
        max_length=100, 
        help_text="Display name of the network provider"
    )
    logo = models.URLField(
        blank=True, 
        help_text="URL to the provider's logo (optional)"
    )
    accent = models.CharField(
        max_length=32,
        blank=True,
        help_text="Provider brand color (hex, rgba, css, optional)"
    )
    active = models.BooleanField(
        default=True,
        help_text="Is the provider currently active and available for selection?"
    )

    class Meta:
        verbose_name = "Network Provider"
        verbose_name_plural = "Network Providers"

    def __str__(self):
        return self.label

class AirtimePurchase(models.Model):
    """
    Model representing a customer airtime purchase order/transaction.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="airtime_purchases",
        help_text="User who made the purchase"
    )
    provider = models.ForeignKey(
        NetworkProvider,
        on_delete=models.PROTECT,
        related_name="airtime_purchases",
        help_text="Mobile network provider"
    )
    phone = models.CharField(
        max_length=15,
        help_text="Phone number recharged (Nigerian format, just digits, e.g. 08011112222)"
    )
    amount = models.PositiveIntegerField(
        help_text="Amount of airtime in Naira (minimum 50, maximum 20000, inclusive)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Time when the airtime purchase was created"
    )
    completed = models.BooleanField(
        default=False,
        help_text="Whether the purchase has been processed/successful"
    )
    external_ref = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        help_text="External transaction reference (if applicable)"
    )
    status_message = models.CharField(
        max_length=1024,
        blank=True,
        help_text="Optional message about transaction status or failure"
    )

    class Meta:
        verbose_name = "Airtime Purchase"
        verbose_name_plural = "Airtime Purchases"
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"Airtime ({self.amount} NGN) for {self.phone} on {self.provider.label} "
            f"by {self.user} [{'Done' if self.completed else 'Pending'}]"
        )


