from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from notification.models import Notification
from app.visa.study.models import StudyVisaApplication
from app.visa.study.offers.models import StudyVisaOffer

def create_study_notification(user, title, message, notification_type="system", data=None):
    if not user:
        return
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        data=data or {},
    )

@receiver(pre_save, sender=StudyVisaApplication)
def study_application_pre_save(sender, instance, **kwargs):
    """
    Attach the old instance or old status to the instance before saving,
    so we can detect status changes and other changes in post_save.
    """
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._old_status_id = old_instance.status_id
            instance._old_is_submitted = old_instance.is_submitted
            instance._old_institution_id = old_instance.institution_id
            instance._old_course_of_study_id = old_instance.course_of_study_id
            instance._old_program_type_id = old_instance.program_type_id
            instance._old_offer_id = old_instance.study_visa_offer_id
        except sender.DoesNotExist:
            instance._old_status_id = None
            instance._old_is_submitted = None
            instance._old_institution_id = None
            instance._old_course_of_study_id = None
            instance._old_program_type_id = None
            instance._old_offer_id = None
    else:
        instance._old_status_id = None
        instance._old_is_submitted = None
        instance._old_institution_id = None
        instance._old_course_of_study_id = None
        instance._old_program_type_id = None
        instance._old_offer_id = None

@receiver(post_save, sender=StudyVisaApplication)
def study_application_post_save(sender, instance, created, **kwargs):
    applicant_user = None
    try:
        applicant_user = instance.applicant.user
    except Exception:
        pass

    # 1. Application created event
    if created:
        offer_title = None
        if instance.study_visa_offer:
            offer_title = instance.study_visa_offer.offer_title
        elif instance.institution:
            offer_title = f"Institution: {instance.institution.name}"
        else:
            offer_title = "your study visa application"
        title = "Study Visa Application Submitted"
        message = f"Your application for '{offer_title}' has been submitted."
        create_study_notification(
            user=applicant_user,
            title=title,
            message=message,
            notification_type="system",
            data={
                "study_visa_application_id": instance.id,
                "event": "application_created",
                "offer_id": instance.study_visa_offer.id if instance.study_visa_offer else None,
            }
        )
        return

    # 2. Status changes
    old_status_id = getattr(instance, "_old_status_id", None)
    new_status_id = instance.status_id

    if old_status_id != new_status_id:
        try:
            from definition.models import TableDropDownDefinition
            old_status = TableDropDownDefinition.objects.get(pk=old_status_id) if old_status_id else None
            new_status = TableDropDownDefinition.objects.get(pk=new_status_id) if new_status_id else None
            new_status_term = new_status.term if new_status else "Status Updated"
            old_status_term = old_status.term if old_status else None
        except Exception:
            new_status_term = "Status Updated"
            old_status_term = None

        title = "Study Visa Application Status Changed"
        if old_status_term:
            message = f"Your study visa application status changed from '{old_status_term}' to '{new_status_term}'."
        else:
            message = f"Your study visa application status updated to '{new_status_term}'."
        create_study_notification(
            user=applicant_user,
            title=title,
            message=message,
            notification_type="system",
            data={
                "study_visa_application_id": instance.id,
                "event": "status_changed",
                "old_status_id": old_status_id,
                "new_status_id": new_status_id,
            }
        )

    # 3. Application submitted
    old_is_submitted = getattr(instance, "_old_is_submitted", False)
    if not old_is_submitted and instance.is_submitted:
        title = "Study Visa Application Submitted"
        offer_title = None
        if instance.study_visa_offer:
            offer_title = instance.study_visa_offer.offer_title
        elif instance.institution:
            offer_title = f"Institution: {instance.institution.name}"
        else:
            offer_title = "your study visa application"
        message = f"Your application for '{offer_title}' has been officially submitted."
        create_study_notification(
            user=applicant_user,
            title=title,
            message=message,
            notification_type="system",
            data={
                "study_visa_application_id": instance.id,
                "event": "application_submitted",
                "offer_id": instance.study_visa_offer.id if instance.study_visa_offer else None,
            }
        )

    # 4. Changes to institution, course, program type or offer
    change_detected = False
    change_fields = []
    field_map = [
        ("institution_id", "_old_institution_id"),
        ("course_of_study_id", "_old_course_of_study_id"),
        ("program_type_id", "_old_program_type_id"),
        ("study_visa_offer_id", "_old_offer_id"),
    ]
    for field, old_field in field_map:
        if getattr(instance, field) != getattr(instance, old_field):
            change_detected = True
            change_fields.append(field.replace("_id", "").replace("_", " ").title())

    if change_detected:
        title = "Application Details Updated"
        changed_str = ", ".join(change_fields)
        message = f"The following details of your study visa application were updated: {changed_str}."
        create_study_notification(
            user=applicant_user,
            title=title,
            message=message,
            notification_type="system",
            data={
                "study_visa_application_id": instance.id,
                "event": "application_details_changed",
                "changed_fields": change_fields,
            }
        )

@receiver(post_delete, sender=StudyVisaApplication)
def study_application_post_delete(sender, instance, **kwargs):
    # Could be deleted by user or admin
    applicant_user = None
    try:
        applicant_user = instance.applicant.user
    except Exception:
        pass
    if applicant_user:
        offer_title = None
        if instance.study_visa_offer:
            offer_title = instance.study_visa_offer.offer_title
        elif instance.institution:
            offer_title = f"Institution: {instance.institution.name}"
        else:
            offer_title = "your study visa application"
        title = "Study Visa Application Deleted"
        message = f"Your application for '{offer_title}' has been deleted."
        create_study_notification(
            user=applicant_user,
            title=title,
            message=message,
            notification_type="system",
            data={
                "study_visa_application_id": instance.id,
                "event": "application_deleted",
                "offer_id": instance.study_visa_offer.id if instance.study_visa_offer else None,
            }
        )

# If you wish, you can add similar signals for StudyVisaOffer for admin notifications,
# but skipping here because offers are usually created/edited by admins, not individual users.

