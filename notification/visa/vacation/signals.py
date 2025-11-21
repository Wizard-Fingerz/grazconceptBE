from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from notification.models import Notification
from app.visa.vacation.offer.models import VacationOffer, VacationVisaApplication

def get_notification_user_from_applicant(applicant):
    """
    Returns the user object related to the applicant for notification purposes.
    Handles direct user or related user (for 'Client' applicant) fallback.
    """
    if hasattr(applicant, 'user') and applicant.user is not None:
        # applicant has a direct user field
        return applicant.user
    elif hasattr(applicant, 'account') and applicant.account is not None:
        # Fallback: some implementations have 'account' pointing to User
        return applicant.account
    elif hasattr(applicant, 'email'):
        # As an absolute fallback (not recommended), just return None
        # or raise, depending on requirements
        return None
    return None

def create_vacation_notification(user, title, message, notification_type="system", data=None):
    if not user:
        return
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        data=data or {},
    )

# --------- VacationOffer signals (optional, mainly admin notifications) ---------
# Notifying staff or all users is not implemented here since no user is directly linked.

@receiver(post_save, sender=VacationOffer)
def vacation_offer_post_save(sender, instance, created, **kwargs):
    # Optionally notify admins/staff about new or updated offers via Notification
    pass

@receiver(post_delete, sender=VacationOffer)
def vacation_offer_post_delete(sender, instance, **kwargs):
    # Optionally notify admins/staff about deleted offers
    pass

# --------- VacationVisaApplication signals ---------

@receiver(pre_save, sender=VacationVisaApplication)
def vacation_application_pre_save(sender, instance, **kwargs):
    """
    Attach old status to the instance, to detect changes in post_save.
    """
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._old_status_id = old_instance.status_id
        except sender.DoesNotExist:
            instance._old_status_id = None
    else:
        instance._old_status_id = None

@receiver(post_save, sender=VacationVisaApplication)
def vacation_application_post_save(sender, instance, created, **kwargs):
    # Application Created Event
    user = get_notification_user_from_applicant(instance.applicant)
    if created:
        title = "Vacation Visa Application Submitted"
        offer_title = instance.offer.title if instance.offer else "the offer"
        message = f"Your application for '{offer_title}' has been submitted successfully."
        create_vacation_notification(
            user=user,
            title=title,
            message=message,
            notification_type="system",
            data={
                "vacation_visa_application_id": instance.id,
                "offer_id": instance.offer.id if instance.offer else None,
                "event": "application_created",
            },
        )
    else:
        # Check for status change
        old_status_id = getattr(instance, "_old_status_id", None)
        new_status_id = instance.status_id
        if old_status_id != new_status_id and new_status_id is not None:
            old_status = None
            new_status = None
            if old_status_id:
                try:
                    from definition.models import TableDropDownDefinition
                    old_status = TableDropDownDefinition.objects.get(pk=old_status_id)
                except Exception:
                    old_status = None
            if instance.status:
                new_status = instance.status
            else:
                new_status = None
            title = "Vacation Visa Application Status Updated"
            offer_title = instance.offer.title if instance.offer else "the offer"
            new_status_display = new_status.term if new_status else "Updated"
            message = (
                f"The status of your vacation visa application for '{offer_title}' "
                f"has changed to '{new_status_display}'."
            )
            create_vacation_notification(
                user=user,
                title=title,
                message=message,
                notification_type="system",
                data={
                    "vacation_visa_application_id": instance.id,
                    "offer_id": instance.offer.id if instance.offer else None,
                    "old_status_id": old_status_id,
                    "new_status_id": new_status_id,
                    "event": "application_status_changed",
                },
            )

@receiver(post_delete, sender=VacationVisaApplication)
def vacation_application_post_delete(sender, instance, **kwargs):
    # If needed, notify user that the application was deleted (by admin or system)
    title = "Vacation Visa Application Deleted"
    offer_title = instance.offer.title if instance.offer else "the offer"
    message = (
        f"Your vacation visa application for '{offer_title}' has been deleted. "
        "If you believe this was a mistake, please contact support."
    )
    user = get_notification_user_from_applicant(instance.applicant)
    if not user:
        return
    create_vacation_notification(
        user=user,
        title=title,
        message=message,
        notification_type="system",
        data={
            "vacation_visa_application_id": instance.id,
            "offer_id": instance.offer.id if instance.offer else None,
            "event": "application_deleted",
        },
    )

