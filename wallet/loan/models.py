from django.db import models
from django.conf import settings
from definition.models import TableDropDownDefinition

class LoanOffer(models.Model):
    """
    Model representing a loan offer that users can apply for.
    The offer defines the available loan product, its requirements, and parameters.
    """

    # Instead of static loan_type choices, use a ForeignKey to TableDropDownDefinition.
    # E.g. the dropdown definition might have keys like "civil_servant", "study", etc.
    loan_type = models.ForeignKey(
        TableDropDownDefinition,
        on_delete=models.PROTECT,
        limit_choices_to= 'loan_type',
        related_name="loan_offers",
        help_text="Dropdown definition record for this loan type (e.g. 'civil_servant', 'study')"
    )

    name = models.CharField(max_length=100, unique=True, help_text="Name of the loan offer")
    description = models.TextField(blank=True, help_text="Description or details about the loan product")
    min_amount = models.DecimalField(
        max_digits=18, decimal_places=2,
        help_text="Minimum allowed amount for this loan offer"
    )
    max_amount = models.DecimalField(
        max_digits=18, decimal_places=2,
        help_text="Maximum allowed amount for this loan offer"
    )
    currency = models.CharField(
        max_length=10,
        default="NGN"
    )
    required_documents = models.TextField(
        blank=True,
        help_text="Comma-separated list or details of documents required"
    )
    requirements = models.TextField(
        blank=True,
        help_text="Eligibility requirements or other notes"
    )
    interest_rate = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="Annual interest rate (%)"
    )
    duration_months = models.PositiveIntegerField(
        help_text="Duration of the loan offer in months"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        # Show the dropdown label, fallback to id if needed
        loan_type_label = getattr(self.loan_type, 'label', None) or str(self.loan_type)
        return f"{self.name} ({loan_type_label})"


class LoanApplication(models.Model):
    """
    Model representing a user's application for a given loan offer.
    Users fill required information and details when applying for a specific loan offer.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='loan_applications',
        on_delete=models.CASCADE
    )
    loan_offer = models.ForeignKey(
        LoanOffer,
        related_name='applications',
        on_delete=models.CASCADE,
        help_text="The loan offer being applied for"
    )
    amount = models.DecimalField(
        max_digits=18, decimal_places=2,
        help_text="Requested loan amount"
    )
    currency = models.CharField(
        max_length=10,
        default="NGN"
    )
    purpose = models.TextField(
        blank=True,
        help_text="Purpose or description of the loan"
    )
    status = models.ForeignKey(
        TableDropDownDefinition,
        on_delete=models.PROTECT,
        limit_choices_to= 'loan_status',
        related_name='loan_application_statuses',
        help_text="Dropdown definition record for the current status of the loan application"
    )
    # You might collect additional info per application:
    filled_details = models.JSONField(
        blank=True,
        null=True,
        help_text="Additional information/details required for this application"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        status_label = getattr(self.status, 'label', None) or str(self.status)
        return f"LoanApplication #{self.id} for {self.loan_offer.name} by {self.user} - {status_label}"

class LoanRepayment(models.Model):
    """
    Model representing a repayment made towards a loan application.
    """
    loan_application = models.ForeignKey(
        LoanApplication,
        related_name='repayments',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='loan_repayments',
        on_delete=models.CASCADE
    )
    amount = models.DecimalField(
        max_digits=18, decimal_places=2,
        help_text="Repayment amount"
    )
    currency = models.CharField(
        max_length=10,
        default="NGN"
    )
    payment_date = models.DateTimeField(auto_now_add=True)
    reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Payment reference or transaction ID"
    )

    def __str__(self):
        return (
            f"Repayment of {self.amount} {self.currency} for LoanApplication #{self.loan_application.id} by {self.user}"
        )
