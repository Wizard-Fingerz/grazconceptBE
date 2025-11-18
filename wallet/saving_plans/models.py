
from django.db import models
from django.conf import settings
from wallet.models import Wallet


class SavingsPlan(models.Model):
    """
    Represents a user's saving plan to fund their wallet.
    """
    PLAN_STATUS = (
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='savings_plans', on_delete=models.CASCADE)
    # The wallet field will automatically use the user wallet, do not expose for form input
    wallet = models.ForeignKey(Wallet, related_name='savings_plans', on_delete=models.CASCADE, editable=False)
    name = models.CharField(max_length=100)
    target_amount = models.DecimalField(max_digits=18, decimal_places=2)
    amount_saved = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=10, default='NGN')
    start_date = models.DateField()
    end_date = models.DateField()
    is_recurring = models.BooleanField(default=False)
    recurrence_period = models.CharField(max_length=20, choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')], blank=True, null=True)
    status = models.CharField(max_length=20, choices=PLAN_STATUS, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    meta = models.JSONField(blank=True, null=True, help_text="Flexible field for extra information.")

    def save(self, *args, **kwargs):
        # Auto-fill the wallet field from user if not provided
        if not self.wallet_id and self.user_id:
            try:
                self.wallet = Wallet.objects.get(user_id=self.user_id)
            except Wallet.DoesNotExist:
                raise ValueError("The user does not have an associated Wallet.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Savings Plan '{self.name}' for {self.user}"

    class Meta:
        ordering = ['-created_at']

