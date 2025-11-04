from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.conf import settings
from wallet.models import Wallet
from notification.models import Notification

import decimal

def create_wallet_notification(user, title, message, notification_type="wallet", data=None):
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        data=data or {},
    )

@receiver(post_save, sender=Wallet)
def wallet_post_save_handler(sender, instance, created, **kwargs):
    """
    Handles Wallet creation and update actions.
    """
    if created:
        # New wallet created for user
        title = "Wallet Created"
        message = f"A new wallet has been created for you with a starting balance of {instance.balance} {instance.currency}."
        create_wallet_notification(
            user=instance.user,
            title=title,
            message=message,
            notification_type="wallet",
            data={"event": "wallet_created", "balance": str(instance.balance), "currency": instance.currency},
        )
    else:
        # Wallet updated: could be fund deposit, withdrawal, etc.
        # To track what exactly changed (like deposit/withdrawal), we check balance change.
        # We need to remember previous balance; so use pre_save to stash old balance

        if hasattr(instance, '_old_balance'):
            old_balance = instance._old_balance
            new_balance = instance.balance

            if new_balance != old_balance:
                diff = decimal.Decimal(new_balance) - decimal.Decimal(old_balance)
                if diff > 0:
                    # Deposit or credit
                    title = "Wallet Credited"
                    message = f"Your wallet has been credited with {diff} {instance.currency}. New balance: {new_balance} {instance.currency}."
                    event = "wallet_credited"
                else:
                    # Withdrawal or debit
                    title = "Wallet Debited"
                    message = f"Your wallet has been debited by {abs(diff)} {instance.currency}. New balance: {new_balance} {instance.currency}."
                    event = "wallet_debited"

                create_wallet_notification(
                    user=instance.user,
                    title=title,
                    message=message,
                    notification_type="wallet",
                    data={"event": event, "old_balance": str(old_balance), "new_balance": str(new_balance)},
                )
                # Remove _old_balance after use to avoid leaks
                del instance._old_balance

        # Status changed (is_active)
        if hasattr(instance, '_old_is_active'):
            old_status = instance._old_is_active
            new_status = instance.is_active
            if old_status != new_status:
                if new_status:
                    title = "Wallet Activated"
                    message = "Your wallet has been activated and is now available for transactions."
                    event = "wallet_activated"
                else:
                    title = "Wallet Deactivated"
                    message = "Your wallet has been deactivated and is no longer available for transactions."
                    event = "wallet_deactivated"

                create_wallet_notification(
                    user=instance.user,
                    title=title,
                    message=message,
                    notification_type="wallet",
                    data={"event": event, "old_status": old_status, "new_status": new_status},
                )
                del instance._old_is_active

@receiver(pre_save, sender=Wallet)
def wallet_pre_save_handler(sender, instance, **kwargs):
    """
    Store old values before save so we can compare in post_save.
    """
    if instance.pk:
        try:
            old_instance = Wallet.objects.get(pk=instance.pk)
            instance._old_balance = old_instance.balance
            instance._old_is_active = old_instance.is_active
        except Wallet.DoesNotExist:
            pass

@receiver(post_delete, sender=Wallet)
def wallet_post_delete_handler(sender, instance, **kwargs):
    """
    Handles Wallet deletion.
    """
    title = "Wallet Deleted"
    message = "Your wallet has been deleted. Please contact support if this was unexpected."
    create_wallet_notification(
        user=instance.user,
        title=title,
        message=message,
        notification_type="wallet",
        data={"event": "wallet_deleted", "balance": str(instance.balance), "currency": instance.currency},
    )
