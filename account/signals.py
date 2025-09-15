from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver

from account.models import User
from account.client.models import Client
from definition.roles.models import Roles
from definition.models import TableDropDownDefinition

def get_customer_client_type():
    """
    Returns the TableDropDownDefinition instance for client_type='Customer'.
    """
    return TableDropDownDefinition.objects.filter(table_name='client_type', term__iexact='JAPA Client').first()

@receiver(post_save, sender=User)
def handle_customer_user(sender, instance, created, **kwargs):
    """
    If the user has a user_type called 'Customer', update their role to 'Customer'
    and create a Client account for them if it doesn't already exist.
    """
    # Check if user_type exists and its term is 'Customer' (case-insensitive)
    if instance.user_type and hasattr(instance.user_type, 'term') and instance.user_type.term and instance.user_type.term.strip().lower() == 'customer':
        # Get or create the 'Customer' role
        customer_role, _ = Roles.objects.get_or_create(name__iexact='customer', defaults={'name': 'Customer'})
        # Update the user's role if not already set
        if instance.role != customer_role:
            instance.role = customer_role
            instance.save(update_fields=['role'])
        # Create a Client account for the user if it doesn't exist
        if not Client.objects.filter(pk=instance.pk).exists():
            client_type = get_customer_client_type()
            if not client_type:
                # Don't create Client if no client_type definition exists
                return
            client = Client.objects.create(
                pk=instance.pk,  # Ensure the Client shares the same PK as User
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
            )
            # service_of_interest and assign_to_teams are M2M, can't set at creation

@receiver(post_migrate)
def create_customer_clients_after_migrate(sender, **kwargs):
    """
    After migrations, ensure all users with user_type 'Customer' have the 'Customer' role
    and a corresponding Client account.
    """
    # Get or create the 'Customer' role
    customer_role, _ = Roles.objects.get_or_create(name__iexact='customer', defaults={'name': 'Customer'})
    client_type = get_customer_client_type()
    if not client_type:
        return
    # Find all users with user_type 'Customer'
    for user in User.objects.filter(user_type__term__iexact='customer'):
        # Update the user's role if not already set
        if user.role != customer_role:
            user.role = customer_role
            user.save(update_fields=['role'])
        # Create a Client account for the user if it doesn't exist
        if not Client.objects.filter(pk=user.pk).exists():
            Client.objects.create(
                pk=user.pk,  # Ensure the Client shares the same PK as User
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
