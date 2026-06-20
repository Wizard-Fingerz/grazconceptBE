from django.db import models
from django.conf import settings


PAYMENT_METHOD_CHOICES = [
    ('wallet', 'Wallet Balance'),
    ('card', 'Debit/Credit Card'),
    ('bank_transfer', 'Bank Transfer'),
    ('mobile_money', 'Mobile Money'),
]

BILL_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('processing', 'Processing'),
    ('successful', 'Successful'),
    ('failed', 'Failed'),
    ('refunded', 'Refunded'),
]


class CableTVSubscription(models.Model):
    """Tracks cable TV / internet subscription payments."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cable_subscriptions',
    )
    provider = models.CharField(max_length=50)           # dstv | gotv | startimes | showmax | spectranet | smile
    provider_label = models.CharField(max_length=100)
    package_code = models.CharField(max_length=100)      # variation_code / plan slug
    package_label = models.CharField(max_length=200)
    iuc_number = models.CharField(max_length=30)         # IUC / account number
    account_name = models.CharField(max_length=200, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='wallet')
    status = models.CharField(max_length=20, choices=BILL_STATUS_CHOICES, default='pending')
    transaction_reference = models.CharField(max_length=100, unique=True)
    flw_tx_ref = models.CharField(max_length=100, blank=True)  # Flutterwave tx ref (card payments)
    flw_transaction_id = models.CharField(max_length=100, blank=True)
    provider_reference = models.CharField(max_length=200, blank=True)
    error_message = models.TextField(blank=True)
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} | {self.provider_label} {self.package_label} | {self.status}"


class BillPaymentRecord(models.Model):
    """
    Generic record for utility / education / other bill payments
    that go through the new value-services endpoints.
    """
    BILL_TYPE_CHOICES = [
        ('electricity', 'Electricity'),
        ('education', 'Education Fees'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bill_payment_records',
    )
    bill_type = models.CharField(max_length=30, choices=BILL_TYPE_CHOICES)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='wallet')
    status = models.CharField(max_length=20, choices=BILL_STATUS_CHOICES, default='pending')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_reference = models.CharField(max_length=100, unique=True)
    flw_tx_ref = models.CharField(max_length=100, blank=True)
    flw_transaction_id = models.CharField(max_length=100, blank=True)
    provider_reference = models.CharField(max_length=200, blank=True)
    token = models.CharField(max_length=200, blank=True)  # prepaid token / education PIN
    error_message = models.TextField(blank=True)
    payload = models.JSONField(default=dict)   # original request fields
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} | {self.bill_type} | {self.status}"
