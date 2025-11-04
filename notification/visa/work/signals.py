from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from notification.models import Notification
from app.visa.work.offers.models import (
    WorkVisaOffer,
    WorkVisaApplication,
    WorkVisaInterview,
    CVSubmission,
)
from django.conf import settings

def create_notification_for_user(user, title, message, notification_type="system", data=None):
    if not user:
        return
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        data=data or {},
    )


# --- WorkVisaOffer signals ---

@receiver(post_save, sender=WorkVisaOffer)
def work_visa_offer_post_save(sender, instance, created, **kwargs):
    # Possible system notification on offer create/update
    if created:
        # Optionally, notify all admin/staff or related recruiters
        title = "New Work Visa Offer Created"
        message = f"A new job offer '{instance.job_title}' at {instance.organization.name} has been created."
        # No user to notify in this context, so skip unless extended
    else:
        # Offer updated
        pass

@receiver(post_delete, sender=WorkVisaOffer)
def work_visa_offer_post_delete(sender, instance, **kwargs):
    # No specific user to notify; could log/delete
    pass


# --- WorkVisaApplication signals ---

@receiver(post_save, sender=WorkVisaApplication)
def work_visa_application_post_save(sender, instance, created, **kwargs):
    if created:
        # Notify client: "Your application has been submitted"
        title = "Work Visa Application Submitted"
        message = f"Your application for '{instance.offer.job_title}' at {instance.offer.organization.name} has been submitted successfully."
        create_notification_for_user(
            user=instance.client,
            title=title,
            message=message,
            notification_type="system",
            data={
                "work_visa_application_id": instance.id,
                "offer_id": instance.offer.id,
                "event": "application_created",
            },
        )
    else:
        # Status changed/updated
        # Only notify if status field has actually changed
        from django.db.models import F
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            old_status_id = getattr(old_instance, "status_id", None)
            new_status_id = getattr(instance, "status_id", None)
        except sender.DoesNotExist:
            old_status_id = None
            new_status_id = instance.status_id

        if old_status_id != new_status_id:
            status_name = getattr(instance.status, "term", "updated")
            title = "Application Status Updated"
            message = (
                f"Your application for '{instance.offer.job_title}' at {instance.offer.organization.name} "
                f"has changed status to '{status_name}'."
            )
            create_notification_for_user(
                user=instance.client,
                title=title,
                message=message,
                notification_type="system",
                data={
                    "work_visa_application_id": instance.id,
                    "offer_id": instance.offer.id,
                    "event": "application_status_changed",
                    "new_status": status_name,
                },
            )

@receiver(post_delete, sender=WorkVisaApplication)
def work_visa_application_post_delete(sender, instance, **kwargs):
    # Notify client: "Your application has been deleted"
    title = "Work Visa Application Deleted"
    message = (
        f"Your application for '{instance.offer.job_title}' at {instance.offer.organization.name}' has been deleted."
    )
    create_notification_for_user(
        user=instance.client,
        title=title,
        message=message,
        notification_type="system",
        data={
            "work_visa_application_id": instance.id,
            "offer_id": instance.offer.id,
            "event": "application_deleted",
        },
    )


# --- WorkVisaInterview signals ---

@receiver(post_save, sender=WorkVisaInterview)
def work_visa_interview_post_save(sender, instance, created, **kwargs):
    app = instance.application
    user = getattr(app, "client", None)
    if created:
        title = "Interview Scheduled"
        message = (
            f"An interview has been scheduled for your application to '{app.offer.job_title}' at {app.offer.organization.name}. "
            f"Date: {instance.interview_date}, Time: {instance.interview_time}."
        )
        event = "interview_scheduled"
    else:
        # Could be status change or update
        title = "Interview Updated"
        message = (
            f"Your interview for '{app.offer.job_title}' at {app.offer.organization.name} is now '{instance.status}'."
        )
        event = "interview_updated"
    create_notification_for_user(
        user=user,
        title=title,
        message=message,
        notification_type="system",
        data={
            "interview_id": instance.id,
            "application_id": app.id,
            "offer_id": app.offer.id,
            "status": instance.status,
            "event": event,
        },
    )


@receiver(post_delete, sender=WorkVisaInterview)
def work_visa_interview_post_delete(sender, instance, **kwargs):
    app = instance.application
    user = getattr(app, "client", None)
    title = "Interview Cancelled"
    message = (
        f"Your interview for '{app.offer.job_title}' at {app.offer.organization.name} has been cancelled."
    )
    create_notification_for_user(
        user=user,
        title=title,
        message=message,
        notification_type="system",
        data={
            "interview_id": instance.id,
            "application_id": app.id,
            "offer_id": app.offer.id,
            "event": "interview_deleted",
        },
    )


# --- CVSubmission signals ---

@receiver(post_save, sender=CVSubmission)
def cv_submission_post_save(sender, instance, created, **kwargs):
    # Notification only if there is a user relation; CV submissions are external but may want confirmation
    if created:
        title = "CV Submitted"
        message = (
            f"Your CV has been submitted for "
            f"'{instance.job.job_title if instance.job else instance.job_title_freeform}' "
            f"({instance.country})."
        )
        # If in future you relate to a user, notify. For now, could email or skip notification.
        # Example: create_notification_for_user(user, ...)
    else:
        # E.g., is_processed -> notify candidate if desired (if user relation is added)
        pass

@receiver(post_delete, sender=CVSubmission)
def cv_submission_post_delete(sender, instance, **kwargs):
    # Optionally notify candidate if user relation exists.
    pass

