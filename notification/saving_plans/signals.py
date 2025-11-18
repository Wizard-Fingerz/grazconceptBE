from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.conf import settings
from wallet.saving_plans.models import SavingsPlan  # Correct import for SavingsPlan
from notification.models import Notification

import decimal

def create_savings_plan_notification(user, title, message, notification_type="saving_plan", data=None):
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        data=data or {},
    )

@receiver(post_save, sender=SavingsPlan)
def savings_plan_post_save_handler(sender, instance, created, **kwargs):
    """
    Handles SavingsPlan creation and update actions.
    """
    if created:
        # New savings plan created
        title = "Savings Plan Created"
        message = f"Your savings plan '{instance.name}' has been created. Target: {instance.target_amount} {instance.currency}, Ends: {instance.end_date}."
        create_savings_plan_notification(
            user=instance.user,
            title=title,
            message=message,
            notification_type="saving_plan",
            data={
                "event": "savings_plan_created",
                "plan_id": instance.id,
                "target_amount": str(instance.target_amount),
                "currency": instance.currency,
                "end_date": str(instance.end_date),
                "name": instance.name,
            },
        )
    else:
        # SavingsPlan updated
        # Track what changed: amount_saved, status, or meta fields

        # Amount saved changed
        if hasattr(instance, "_old_amount_saved"):
            old_saved = instance._old_amount_saved
            new_saved = instance.amount_saved
            if new_saved != old_saved:
                diff = decimal.Decimal(new_saved) - decimal.Decimal(old_saved)
                if diff > 0:
                    action = "incremented"
                    event = "amount_saved_increased"
                else:
                    action = "decremented"
                    event = "amount_saved_decreased"

                title = "Savings Plan Progress Updated"
                message = (
                    f"Your savings plan '{instance.name}' amount_saved has been {action} by {abs(diff)} {instance.currency}. "
                    f"New saved amount: {new_saved} {instance.currency}."
                )
                create_savings_plan_notification(
                    user=instance.user,
                    title=title,
                    message=message,
                    notification_type="saving_plan",
                    data={
                        "event": event,
                        "plan_id": instance.id,
                        "name": instance.name,
                        "old_amount_saved": str(old_saved),
                        "new_amount_saved": str(new_saved),
                        "currency": instance.currency,
                    }
                )
            del instance._old_amount_saved

        # Status changed
        if hasattr(instance, "_old_status"):
            old_status = instance._old_status
            new_status = instance.status
            if old_status != new_status:
                if new_status == "completed":
                    title = "Savings Plan Completed"
                    message = f"Congratulations! Your savings plan '{instance.name}' has been completed."
                    event = "savings_plan_completed"
                elif new_status == "cancelled":
                    title = "Savings Plan Cancelled"
                    message = f"Your savings plan '{instance.name}' has been cancelled."
                    event = "savings_plan_cancelled"
                elif new_status == "active" and old_status != "active":
                    title = "Savings Plan Activated"
                    message = f"Your savings plan '{instance.name}' has been re-activated."
                    event = "savings_plan_activated"
                else:
                    title = f"Savings Plan status changed"
                    message = f"Your savings plan '{instance.name}' status changed from '{old_status}' to '{new_status}'."
                    event = "savings_plan_status_changed"

                create_savings_plan_notification(
                    user=instance.user,
                    title=title,
                    message=message,
                    notification_type="saving_plan",
                    data={
                        "event": event,
                        "plan_id": instance.id,
                        "old_status": old_status,
                        "new_status": new_status,
                        "name": instance.name,
                    }
                )
            del instance._old_status

@receiver(pre_save, sender=SavingsPlan)
def savings_plan_pre_save_handler(sender, instance, **kwargs):
    """
    Stash old values before save to detect changes in post_save.
    """
    if instance.pk:
        try:
            old_instance = SavingsPlan.objects.get(pk=instance.pk)
            instance._old_amount_saved = old_instance.amount_saved
            instance._old_status = old_instance.status
        except SavingsPlan.DoesNotExist:
            pass

@receiver(post_delete, sender=SavingsPlan)
def savings_plan_post_delete_handler(sender, instance, **kwargs):
    """
    Handles SavingsPlan deletion.
    """
    title = "Savings Plan Deleted"
    message = f"Your savings plan '{instance.name}' has been deleted."
    create_savings_plan_notification(
        user=instance.user,
        title=title,
        message=message,
        notification_type="saving_plan",
        data={
            "event": "savings_plan_deleted",
            "plan_id": instance.id,
            "name": instance.name,
            "target_amount": str(instance.target_amount),
            "amount_saved": str(instance.amount_saved),
            "currency": instance.currency,
        }
    )
