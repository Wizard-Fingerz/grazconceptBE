from django.db import models
from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from .models import WalletTransaction
from wallet.models import Wallet
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=WalletTransaction)
def process_wallet_transaction_on_success(sender, instance, created, **kwargs):
    """
    Process the wallet transaction and update wallet balance when a WalletTransaction
    is created or updated and its status is 'successful', AND it either:
      - is newly created with status 'successful'
      - or transitioned from a non-successful status to 'successful'
    The balance verification and correction for all wallets is NOT performed here;
    it's only for the affected wallet for this instance.
    """
    if instance.status != 'successful':
        return

    # Check if created as 'successful' or updated to 'successful'
    # (We want to run only on a transition to 'successful')
    should_process = False
    if created:
        should_process = True
    else:
        try:
            old = WalletTransaction.objects.get(pk=instance.pk)
        except WalletTransaction.DoesNotExist:
            old = None
        should_process = (
            old is not None and
            old.status != 'successful'
        )
    if created or should_process:
        try:
            instance.process_transaction()
        except Exception as e:
            logger.error(f"Error processing wallet transaction {instance.pk}: {str(e)}")
            raise e

@receiver(post_migrate)
def reconcile_all_wallet_balances(sender, **kwargs):
    """
    After migrations, verify and update all wallet balances to match the total
    of successful transactions for each wallet.
    """
    try:
        for wallet in Wallet.objects.all():
            total_successful_deposit = WalletTransaction.objects.filter(
                wallet=wallet, status='successful', transaction_type='deposit'
            ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')

            total_successful_withdrawal = WalletTransaction.objects.filter(
                wallet=wallet, status='successful', transaction_type='withdrawal'
            ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')

            total_successful_transfer = WalletTransaction.objects.filter(
                wallet=wallet, status='successful', transaction_type='transfer'
            ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')

            total_successful_payment = WalletTransaction.objects.filter(
                wallet=wallet, status='successful', transaction_type='payment'
            ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')

            total_successful_refund = WalletTransaction.objects.filter(
                wallet=wallet, status='successful', transaction_type='refund'
            ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')

            total_successful_savings_funding = WalletTransaction.objects.filter(
                wallet=wallet, status='successful', transaction_type='savings_funding'
            ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')

            # Apply business logic from process_transaction accounting
            wallet_expected_balance = (
                total_successful_deposit
                + total_successful_refund
                - total_successful_withdrawal
                - total_successful_transfer
                - total_successful_payment
                - total_successful_savings_funding
            )
            # Compare and update if necessary
            if wallet.balance != wallet_expected_balance:
                logger.warning(
                    f"Wallet {wallet.id} balance discrepancy detected after migration. "
                    f"Current: {wallet.balance}, Expected: {wallet_expected_balance}. "
                    f"Updating balance to match successful transactions."
                )
                wallet.balance = wallet_expected_balance
                wallet.save(update_fields=["balance"])
    except Exception as e:
        logger.error(f"Error verifying/updating wallet balances after migration: {str(e)}")
