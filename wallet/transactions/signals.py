from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import WalletTransaction

@receiver(post_save, sender=WalletTransaction)
def process_wallet_transaction_on_success(sender, instance, created, **kwargs):
    """
    Process the wallet transaction and update wallet balance when a WalletTransaction
    is created or updated and its status is 'successful', AND it either:
      - is newly created with status 'successful'
      - or transitioned from a non-successful status to 'successful' (handled below)
    """
    # To avoid double processing, use an internal flag on the instance per request if needed
    # But with post_save, we need to detect if the status just became 'successful'

    # Only process actual successful transactions
    if instance.status != 'successful':
        return

    # Check if created as 'successful' or updated to 'successful'
    if created:
        should_process = True
    else:
        # Fetch previous value from DB to see if status just transitioned to 'successful'
        try:
            old = WalletTransaction.objects.get(pk=instance.pk)
        except WalletTransaction.DoesNotExist:
            old = None
        # If old exists and was not successful previously, and now is, process
        # But post_save receives the updated instance, so we need to check the 'old' before the update
        # However, if it is not created and old.status != 'successful', process
        should_process =(
            old is not None and
            old.status != 'successful'
        )

    # Only process once
    if (created or should_process):
        try:
            instance.process_transaction()
        except Exception as e:
            # You may want to log this exception or handle accordingly
            raise e

