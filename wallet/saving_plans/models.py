
from django.db import models
from django.conf import settings
from wallet.models import Wallet
from datetime import timedelta, date

class SavingsPlan(models.Model):
    """
    Represents a user's saving plan to fund their wallet.
    Automatically calculates deduction amount for recurring plans.
    Supports plan cancellation.
    """
    PLAN_STATUS = (
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    RECURRENCE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]

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
    recurrence_period = models.CharField(
        max_length=20,
        choices=RECURRENCE_CHOICES,
        blank=True, null=True
    )
    deduction_amount = models.DecimalField(
        max_digits=18, decimal_places=2, blank=True, null=True,
        help_text="How much should be debited for each recurring interval"
    )
    status = models.CharField(max_length=20, choices=PLAN_STATUS, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    meta = models.JSONField(blank=True, null=True, help_text="Flexible field for extra information.")

    def calculate_deduction_amount(self):
        """
        Calculate the deduction amount per period for recurring plans.
        """
        if not self.is_recurring or not self.recurrence_period or not self.start_date or not self.end_date:
            return None
        total = float(self.target_amount)
        freq_num = 1
        if self.recurrence_period == 'daily':
            freq_num = (self.end_date - self.start_date).days + 1
        elif self.recurrence_period == 'weekly':
            freq_num = max(1, ((self.end_date - self.start_date).days // 7) + (1 if (self.end_date - self.start_date).days % 7 else 0))
        elif self.recurrence_period == 'monthly':
            freq_num = max(1, (self.end_date.year - self.start_date.year) * 12 + (self.end_date.month - self.start_date.month) + (1 if self.end_date.day >= self.start_date.day else 0))
        if freq_num <= 0:
            freq_num = 1
        # Always round up to at least two decimal places
        from decimal import Decimal, ROUND_UP
        deduction = Decimal(total/freq_num).quantize(Decimal('0.01'), rounding=ROUND_UP)
        return deduction

    def save(self, *args, **kwargs):
        # Auto-fill the wallet field from user if not provided
        if not self.wallet_id and self.user_id:
            try:
                self.wallet = Wallet.objects.get(user_id=self.user_id)
            except Wallet.DoesNotExist:
                raise ValueError("The user does not have an associated Wallet.")

        # Calculate deduction_amount for recurring plans
        if self.is_recurring and self.recurrence_period:
            self.deduction_amount = self.calculate_deduction_amount()
        else:
            self.deduction_amount = None

        super().save(*args, **kwargs)

    def cancel(self):
        """
        Cancels the saving plan if active.
        """
        if self.status != 'cancelled':
            self.status = 'cancelled'
            self.save(update_fields=['status', 'updated_at'])

    def __str__(self):
        return f"Savings Plan '{self.name}' for {self.user}"

    class Meta:
        ordering = ['-created_at']

