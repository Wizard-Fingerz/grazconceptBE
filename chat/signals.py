from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver

from django.contrib.auth import get_user_model

try:
    from chat.models import ChatSession
except ImportError:
    ChatSession = None  # Guard for migration time

User = get_user_model()


def should_create_for_user(user):
    """
    Helper to determine if we should create ChatSessions for a given user.
    Only creates for customers/clients; not admins/staff.
    """
    # Only create a chat session for users of type 'client' or similar
    if hasattr(user, 'user_type_name'):
        utype = user.user_type_name
        if utype and utype.lower() not in ("client", "customer"):
            return False

    # Do not auto-create for superusers or staff/admin
    if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
        return False

    return True


def get_all_admins():
    """
    Returns a queryset of all admin users (superusers or staff).
    """
    return User.objects.filter(is_superuser=True) | User.objects.filter(is_staff=True)


@receiver(post_save, sender=User)
def auto_create_chat_sessions_for_user(sender, instance, created, **kwargs):
    """
    Automatically create ChatSessions for a new eligible customer, 
    with every admin as an agent.
    """
    if not created or not ChatSession:
        return

    if should_create_for_user(instance):
        admins = get_all_admins().distinct()
        if admins.exists():
            for admin in admins:
                if not ChatSession.objects.filter(customer=instance, agent=admin).exists():
                    ChatSession.objects.create(customer=instance, agent=admin)
        else:
            # Fallback: create a session with no agent if no admins are present
            if not ChatSession.objects.filter(customer=instance, agent=None).exists():
                ChatSession.objects.create(customer=instance, agent=None)


@receiver(post_migrate)
def auto_create_chat_sessions_for_existing_users(sender, **kwargs):
    """
    After migrations, ensure every eligible customer has a ChatSession
    with every admin.
    """
    if not ChatSession:
        return

    admins = get_all_admins().distinct()
    for user in User.objects.all():
        if should_create_for_user(user):
            if admins.exists():
                for admin in admins:
                    if not ChatSession.objects.filter(customer=user, agent=admin).exists():
                        ChatSession.objects.create(customer=user, agent=admin)
            else:
                # Fallback: create a session with no agent if no admins are present
                if not ChatSession.objects.filter(customer=user, agent=None).exists():
                    ChatSession.objects.create(customer=user, agent=None)
