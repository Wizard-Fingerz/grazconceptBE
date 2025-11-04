from django.db import models
from django.conf import settings
from wallet.models import Wallet
from wallet.saving_plans.models import SavingsPlan
from django.db import transaction as db_transaction  # For atomic wallet updates

# Do NOT import PaymentGateway here to avoid circular import issues

class WalletTransaction(models.Model):
    """
    Represents all wallet-related financial transactions.
    """
    TYPE_CHOICES = (
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('transfer', 'Transfer'),
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('savings_funding', 'Savings Funding'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='wallet_transactions', on_delete=models.CASCADE)
    wallet = models.ForeignKey(Wallet, related_name='transactions', on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    currency = models.CharField(max_length=10, default="NGN")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reference = models.CharField(max_length=128, unique=True)
    # Use a string reference to avoid circular import
    payment_gateway = models.ForeignKey(
        'PaymentGateway',
        related_name='transactions',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    meta = models.JSONField(blank=True, null=True, help_text="Flexible data for storing raw gateway responses, etc.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    savings_plan = models.ForeignKey(
        SavingsPlan, 
        related_name='transactions', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        help_text='If the transaction is related to a saving plan'
    )

    def __str__(self):
        return f"{self.transaction_type.title()} of {self.amount} {self.currency} by {self.user} ({self.status})"

    def process_deposit(self):
        if self.transaction_type != 'deposit':
            raise ValueError("Transaction type must be 'deposit' to process deposit.")
        if self.status != 'successful':
            raise ValueError("Only successful transactions can be processed for wallet funding.")

        with db_transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(pk=self.wallet.pk)
            wallet.balance = wallet.balance + self.amount
            wallet.save()

    def process_withdrawal(self):
        if self.transaction_type != 'withdrawal':
            raise ValueError("Transaction type must be 'withdrawal' to process withdrawal.")
        if self.status != 'successful':
            raise ValueError("Only successful transactions can be processed for wallet withdrawal.")

        with db_transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(pk=self.wallet.pk)
            if wallet.balance < self.amount:
                raise ValueError("Insufficient funds in wallet for withdrawal.")
            wallet.balance = wallet.balance - self.amount
            wallet.save()

    def process_transfer(self):
        if self.transaction_type != 'transfer':
            raise ValueError("Transaction type must be 'transfer' to process transfer.")
        if self.status != 'successful':
            raise ValueError("Only successful transactions can be processed for wallet transfer.")

        with db_transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(pk=self.wallet.pk)
            if wallet.balance < self.amount:
                raise ValueError("Insufficient funds in wallet for transfer.")
            wallet.balance = wallet.balance - self.amount
            wallet.save()

    def process_payment(self):
        if self.transaction_type != 'payment':
            raise ValueError("Transaction type must be 'payment' to process payment.")
        if self.status != 'successful':
            raise ValueError("Only successful transactions can be processed for wallet payment.")

        with db_transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(pk=self.wallet.pk)
            if wallet.balance < self.amount:
                raise ValueError("Insufficient funds in wallet for payment.")
            wallet.balance = wallet.balance - self.amount
            wallet.save()

    def process_refund(self):
        if self.transaction_type != 'refund':
            raise ValueError("Transaction type must be 'refund' to process refund.")
        if self.status != 'successful':
            raise ValueError("Only successful transactions can be processed for wallet refund.")

        with db_transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(pk=self.wallet.pk)
            wallet.balance = wallet.balance + self.amount
            wallet.save()

    def process_savings_funding(self):
        if self.transaction_type != 'savings_funding':
            raise ValueError("Transaction type must be 'savings_funding' to process savings funding.")
        if self.status != 'successful':
            raise ValueError("Only successful transactions can be processed for savings funding.")

        with db_transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(pk=self.wallet.pk)
            if wallet.balance < self.amount:
                raise ValueError("Insufficient funds in wallet for savings funding.")
            wallet.balance = wallet.balance - self.amount
            wallet.save()

    def process_transaction(self):
        if self.status != 'successful':
            raise ValueError("Only successful transactions can be processed for wallet balance adjustments.")

        if self.transaction_type == 'deposit':
            self.process_deposit()
        elif self.transaction_type == 'withdrawal':
            self.process_withdrawal()
        elif self.transaction_type == 'transfer':
            self.process_transfer()
        elif self.transaction_type == 'payment':
            self.process_payment()
        elif self.transaction_type == 'refund':
            self.process_refund()
        elif self.transaction_type == 'savings_funding':
            self.process_savings_funding()
        else:
            raise ValueError(f"Unknown transaction type: {self.transaction_type}")

    def save(self, *args, **kwargs):
        # Determine whether this is a new transaction or an update
        is_new = self._state.adding
        old_status = None
        old_type = None
        if not is_new and self.pk:
            # Fetch the previous object to see if status/type has changed
            previous = type(self).objects.get(pk=self.pk)
            old_status = previous.status
            old_type = previous.transaction_type

        # Save the transaction first to ensure it has an ID/reference, etc.
        super().save(*args, **kwargs)

        # Only process wallet balance when status transitions to 'successful'
        should_process = False
        if is_new:
            # If created directly as 'successful', process immediately
            if self.status == 'successful':
                should_process = True
        else:
            # If an update changed the status to 'successful', process now
            if self.status == 'successful' and (old_status != 'successful'):
                should_process = True

        # Only process once
        if should_process:
            try:
                self.process_transaction()
            except Exception as e:
                # Optionally, re-raise or log for admin feedback
                raise e

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['reference']),
        ]

