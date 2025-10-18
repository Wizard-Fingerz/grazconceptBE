from django.db import models
from django.conf import settings

class LoanApplication(models.Model):
    """
    Model representing a loan application made by a user.
    Can be either a Civil Servant application or a Study application.
    """

    LOAN_TYPE_CIVIL_SERVANT = "civil_servant"
    LOAN_TYPE_STUDY = "study"
    LOAN_TYPE_CHOICES = [
        (LOAN_TYPE_CIVIL_SERVANT, "Civil Servant"),
        (LOAN_TYPE_STUDY, "Study"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name='loan_applications',
        on_delete=models.CASCADE
    )
    loan_type = models.CharField(
        max_length=30,
        choices=LOAN_TYPE_CHOICES,
        default=LOAN_TYPE_CIVIL_SERVANT,
        help_text="Type of loan application: Civil Servant or Study"
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
    status_choices = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("disbursed", "Disbursed"),
        ("repaid", "Repaid")
    ]
    status = models.CharField(
        max_length=20,
        choices=status_choices,
        default="pending"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"LoanApplication #{self.id} ({self.get_loan_type_display()}) by {self.user} - {self.status}"

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
