from django.db import models
from django.conf import settings
from definition.models import TableDropDownDefinition


class EducationFeeProvider(models.Model):
    """
    Exam/Education Provider, e.g., WAEC, NECO, NABTEB, JAMB, University, Others.
    Instead of static choices, the machine key of the provider comes as a FK to TableDropdownDefinition.
    """

    key = models.ForeignKey(
        TableDropDownDefinition,
        on_delete=models.PROTECT,
        related_name="education_fee_providers",
        help_text="Dropdown definition record for this provider (e.g. 'waec', 'university')"
    )
    label = models.CharField(max_length=100, help_text="Display name of the provider")
    logo_url = models.URLField(blank=True, help_text="URL to the provider logo image")
    color = models.CharField(max_length=32, blank=True, help_text="Provider brand color (hex, rgba, css)")

    class Meta:
        verbose_name = "Education/Exam Provider"
        verbose_name_plural = "Education/Exam Providers"
    
    def __str__(self):
        return self.label


class EducationFeeType(models.Model):
    """
    Type of Fee under a Provider, e.g. 'WAEC Registration', 'Acceptance Fee', 'School Fees', etc.
    """
    provider = models.ForeignKey(
        EducationFeeProvider,
        related_name="fee_types",
        on_delete=models.CASCADE
    )
    value = models.CharField(
        max_length=80,
        help_text="Key used to identify fee type, e.g. 'waec_reg', 'uni_accept'"
    )
    label = models.CharField(max_length=128, help_text="Display name, e.g. 'WAEC Registration'")
    min_amount = models.PositiveIntegerField(default=1000, help_text="Minimum payable amount for this fee, in Naira")
    max_amount = models.PositiveIntegerField(blank=True, null=True, help_text="Maximum amount, if any")
    default_amount = models.PositiveIntegerField(blank=True, null=True, help_text="Suggested or typical default fee amount, if any")

    class Meta:
        unique_together = ('provider', 'value')
        verbose_name = "Education Fee Type"
        verbose_name_plural = "Education Fee Types"
    
    def __str__(self):
        return f"{self.provider.label} - {self.label}"


class EducationFeePayment(models.Model):
    """
    Record of a single payment for exam/education fee by a user.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="education_fee_payments",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who made the payment (nullable for guest/unregistered)"
    )
    provider = models.ForeignKey(
        EducationFeeProvider,
        on_delete=models.PROTECT,
        related_name="payments"
    )
    fee_type = models.ForeignKey(
        EducationFeeType,
        on_delete=models.PROTECT,
        related_name="payments"
    )
    candidate_name = models.CharField(max_length=120, help_text="Candidate/Student full name")
    reg_no = models.CharField(max_length=64, blank=True, help_text="Registration/Exam number (if any)")
    amount = models.PositiveIntegerField(help_text="Amount paid in Naira")
    transaction_ref = models.CharField(max_length=100, blank=True, help_text="Transaction or payment gateway reference")
    status = models.CharField(
        max_length=20,
        default="pending",
        choices=[
            ("pending", "Pending"),
            ("success", "Success"),
            ("failed", "Failed"),
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Education Fee Payment"
        verbose_name_plural = "Education Fee Payments"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.candidate_name} | {self.provider.label} | {self.fee_type.label} | ₦{self.amount}"

