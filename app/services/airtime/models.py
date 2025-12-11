from django.db import models
from django.conf import settings

class NetworkProvider(models.Model):
    """
    Model representing a mobile network provider for airtime and data services.
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


class DataPlan(models.Model):
    """
    Represents an available mobile data plan for a given network/provider.
    """
    CATEGORY_CHOICES = (
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
    )

    provider = models.ForeignKey(
        NetworkProvider,
        on_delete=models.CASCADE,
        related_name="data_plans",
        help_text="Mobile network provider for this data plan"
    )
    label = models.CharField(
        max_length=100,
        help_text="Human friendly label for the plan (e.g. '1GB (1 Day)')"
    )
    value = models.CharField(
        max_length=64,
        unique=True,
        help_text="Internal value/identifier for the plan (e.g. 'mtn_1gb_1day')"
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        help_text="Bundle duration category"
    )
    data = models.CharField(
        max_length=20,
        help_text="Data size included in the plan (e.g. '1GB', '500MB')"
    )
    amount = models.PositiveIntegerField(
        help_text="Price of the plan (in Naira)"
    )
    logo = models.CharField(
        max_length=256,
        blank=True,
        help_text="Path or URL to provider logo (optional, for frontend use)"
    )
    accent = models.CharField(
        max_length=16,
        blank=True,
        help_text="Hex color accent for provider (optional, for frontend use)"
    )

    class Meta:
        verbose_name = "Data Plan"
        verbose_name_plural = "Data Plans"
        ordering = ("provider", "amount", "data")

    def __str__(self):
        return f"{self.label} ({self.provider.label}) — {self.amount} NGN"


class DataPurchase(models.Model):
    """
    Model representing a customer data plan purchase/transaction.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="data_purchases",
        help_text="User who made the data plan purchase"
    )
    provider = models.ForeignKey(
        NetworkProvider,
        on_delete=models.PROTECT,
        related_name="data_purchases",
        help_text="Mobile network provider"
    )
    plan = models.ForeignKey(
        DataPlan,
        on_delete=models.PROTECT,
        related_name="purchases",
        help_text="Selected data plan"
    )
    phone = models.CharField(
        max_length=15,
        help_text="Phone number for data activation (Nigerian format, just digits, e.g. 08011112222)"
    )
    amount = models.PositiveIntegerField(
        help_text="Amount paid for data plan (in Naira)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Time when the data plan purchase was created"
    )
    completed = models.BooleanField(
        default=False,
        help_text="Whether the data purchase has been processed/successful"
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
        verbose_name = "Data Purchase"
        verbose_name_plural = "Data Purchases"
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"Data ({self.plan.label}, {self.amount} NGN) for {self.phone} on {self.provider.label} "
            f"by {self.user} [{'Done' if self.completed else 'Pending'}]"
        )



