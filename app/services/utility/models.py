from django.db import models
from django.conf import settings

class UtilityProvider(models.Model):
    """
    Represents an electricity or utility service provider (e.g., Ikeja Electric).
    """
    label = models.CharField(max_length=64, unique=True, help_text="Provider display name, e.g. Ikeja Electric")
    value = models.CharField(max_length=64, unique=True, help_text="Provider code for API, e.g. ikeja_electric")
    logo = models.CharField(max_length=256, blank=True, help_text="Logo asset path or URL")
    accent = models.CharField(max_length=16, blank=True, help_text="Brand accent color HEX code")

    def __str__(self):
        return self.label

class UtilityMeterType(models.TextChoices):
    PREPAID = "prepaid", "Prepaid"
    POSTPAID = "postpaid", "Postpaid"

class UtilityBillPayment(models.Model):
    """
    A record of a single utility bill payment (e.g. for electricity).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="utility_bill_payments"
    )
    provider = models.ForeignKey(UtilityProvider, on_delete=models.PROTECT, related_name="bill_payments")
    meter_type = models.CharField(max_length=16, choices=UtilityMeterType.choices)
    meter_number = models.CharField(max_length=64)
    amount = models.PositiveIntegerField(help_text="Amount paid in Naira")
    status = models.CharField(
        max_length=24,
        choices=[
            ("pending", "Pending"),
            ("success", "Success"),
            ("failed", "Failed"),
        ],
        default="pending"
    )
    transaction_reference = models.CharField(max_length=128, blank=True, null=True, unique=True)
    token = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        help_text="Meter recharge token if prepaid"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user or "Guest"} - {self.provider.label} - {self.meter_number} - ₦{self.amount} ({self.get_status_display()})'
