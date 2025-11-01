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
        """
        Process a deposit transaction: add the transaction amount to the wallet
        and update the wallet's balance. This should only be called when the
        deposit is successful, i.e., after payment gateway confirmation.
        """
        if self.transaction_type != 'deposit':
            raise ValueError("Transaction type must be 'deposit' to process deposit.")
        if self.status != 'successful':
            raise ValueError("Only successful transactions can be processed for wallet funding.")

        with db_transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(pk=self.wallet.pk)
            wallet.balance = wallet.balance + self.amount
            wallet.save()

    def process_withdrawal(self):
        """
        Process a withdrawal transaction: subtract the transaction amount from the wallet
        and update the wallet's balance. This should only be called when the
        withdrawal is successful, i.e., after the money has been sent to user.
        """
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
        """
        Process a transfer transaction: subtract the transaction amount from the sender's wallet
        and typically add it to the recipient's wallet. Here, only process the sender side.
        """
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
        """
        Process a payment transaction: subtract the transaction amount from the wallet,
        typically for paying a bill, service, etc.
        """
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
        """
        Process a refund transaction: add the transaction amount to the wallet,
        representing money returned to the user.
        """
        if self.transaction_type != 'refund':
            raise ValueError("Transaction type must be 'refund' to process refund.")
        if self.status != 'successful':
            raise ValueError("Only successful transactions can be processed for wallet refund.")

        with db_transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(pk=self.wallet.pk)
            wallet.balance = wallet.balance + self.amount
            wallet.save()

    def process_savings_funding(self):
        """
        Process a savings funding transaction: subtract the transaction amount from the wallet
        (to move into savings). Any logic for crediting the savings plan would be handled elsewhere.
        """
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
        """
        Process this transaction and apply its effect to the wallet's balance,
        depending on its transaction_type.
        """
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

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['reference']),
        ]

