from django.db import models
from django.conf import settings

from definition.models import TableDropDownDefinition

class InvestmentPlan(models.Model):
    """
    Defines available investment plans/packages for citizenship-by-investment programs.
    """
    name = models.CharField(max_length=80, unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2, help_text="Minimum investment amount in USD")
    roi_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, help_text="Annual ROI as a % (e.g., 12.00 for 12%)"
    )
    period_months = models.PositiveIntegerField(help_text="Investment period in months")
    color = models.CharField(max_length=24, blank=True, null=True)
    progress = models.PositiveIntegerField(default=0, help_text="General plan progress/uptake (%), not for user")
    withdraw_available = models.BooleanField(default=False)
    warning_note = models.TextField(blank=True, null=True)
    docs_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

class InvestmentPlanBenefit(models.Model):
    """
    Benefits associated with each InvestmentPlan.
    """
    plan = models.ForeignKey(InvestmentPlan, related_name="benefits", on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.plan.name}: {self.text}"

class Investment(models.Model):
    """
    User's active or historical investment in an InvestmentPlan.
    """
    investor = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="investments", on_delete=models.CASCADE
    )
    plan = models.ForeignKey(InvestmentPlan, related_name="investments", on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    roi_amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text="Expected ROI at maturity (can be recalculated as needed)",
        default=0
    )
    start_date = models.DateField()
    maturity_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    withdrawable = models.BooleanField(default=False)
    # Date after which withdrawal is possible (usually == maturity_date)
    next_withdraw_date = models.DateField()

    status = models.ForeignKey(
        TableDropDownDefinition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='investment_statuses',
        limit_choices_to={'table_name': 'investment_status'},
        help_text="Status of this investment from TableDropDownDefinition (e.g. Active, Completed, Withdrawn, Cancelled)",
        default=None,
    )

    def __str__(self):
        return f"{self.investor} - {self.plan.name} (${self.amount})"

    @property
    def is_matured(self):
        from django.utils import timezone
        return timezone.now().date() >= self.maturity_date

    @property
    def can_withdraw(self):
        from django.utils import timezone
        return self.withdrawable and timezone.now().date() >= self.next_withdraw_date

    @property
    def formatted_period(self):
        return f"{self.start_date} - {self.maturity_date}"

    @property
    def status_name(self):
        return self.status.term if self.status else None

    def save(self, *args, **kwargs):
        # Auto-calculate ROI amount when saving, if not set
        if not self.roi_amount and self.plan:
            self.roi_amount = float(self.amount) * float(self.plan.roi_percentage) * (self.plan.period_months/12) / 100
        super().save(*args, **kwargs)
