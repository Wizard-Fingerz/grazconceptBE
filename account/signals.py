from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver

from account.models import User, UserProfile
from account.client.models import Client
from definition.roles.models import Roles
from definition.models import TableDropDownDefinition


def get_customer_client_type():
    return TableDropDownDefinition.objects.filter(
        table_name='client_type', term__iexact='JAPA Client'
    ).first()


@receiver(post_save, sender=User)
def create_user_extended_profile(sender, instance, created, **kwargs):
    """Auto-create UserProfile when a new User is saved."""
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def handle_customer_user(sender, instance, created, **kwargs):
    """
    If the user has a user_type called 'Customer', update their role to 'Customer'
    and create a Client account for them if it doesn't already exist.
    """
    if not (instance.user_type and hasattr(instance.user_type, 'term')):
        return
    if not (instance.user_type.term and instance.user_type.term.strip().lower() == 'customer'):
        return

    customer_role, _ = Roles.objects.get_or_create(
        name__iexact='customer', defaults={'name': 'Customer'}
    )
    if instance.role != customer_role:
        instance.role = customer_role
        instance.save(update_fields=['role'])

    if not Client.objects.filter(pk=instance.pk).exists():
        client_type = get_customer_client_type()
        if not client_type:
            return
        Client.objects.create(
            pk=instance.pk,
            client_type=client_type,
            country=getattr(instance, 'country', None),
            is_prospect=False,
            first_name=instance.first_name,
            middle_name=instance.middle_name,
            last_name=instance.last_name,
            phone_number=instance.phone_number,
            date_of_birth=instance.date_of_birth,
            gender=instance.gender,
            user_type=instance.user_type,
            role=customer_role,
            custom_id=instance.custom_id,
            profile_picture=instance.profile_picture,
            email=instance.email,
            is_deleted=instance.is_deleted,
            is_active=instance.is_active,
            created_by=instance.created_by,
            created_date=instance.created_date,
            modified_by=instance.modified_by,
            modified_date=instance.modified_date,
            last_login=instance.last_login,
            is_staff=instance.is_staff,
            password=instance.password,
        )


@receiver(post_migrate)
def create_customer_clients_after_migrate(sender, **kwargs):
    """
    After migrations, ensure all Customer users have the Customer role
    and a corresponding Client record.
    """
    customer_role, _ = Roles.objects.get_or_create(
        name__iexact='customer', defaults={'name': 'Customer'}
    )
    client_type = get_customer_client_type()
    if not client_type:
        return

    for user in User.objects.filter(user_type__term__iexact='customer'):
        # Ensure extended profile exists
        UserProfile.objects.get_or_create(user=user)

        if user.role != customer_role:
            user.role = customer_role
            user.save(update_fields=['role'])

        if not Client.objects.filter(pk=user.pk).exists():
            Client.objects.create(
                pk=user.pk,
                client_type=client_type,
                country=getattr(user, 'country', None),
                is_prospect=False,
                first_name=user.first_name,
                middle_name=user.middle_name,
                last_name=user.last_name,
                phone_number=user.phone_number,
                date_of_birth=user.date_of_birth,
                gender=user.gender,
                user_type=user.user_type,
                role=customer_role,
                custom_id=user.custom_id,
                profile_picture=user.profile_picture,
                email=user.email,
                is_deleted=user.is_deleted,
                is_active=user.is_active,
                created_by=user.created_by,
                created_date=user.created_date,
                modified_by=user.modified_by,
                modified_date=user.modified_date,
                last_login=user.last_login,
                is_staff=user.is_staff,
            )
