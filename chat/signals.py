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
    Helper to determine if we should create a ChatSession for a given user.
    Mimics the logic in the post_save signal.
    """
    # Only create a chat session for users of type 'client' or similar
    if hasattr(user, 'user_type_name'):
        utype = user.user_type_name
        if utype and utype.lower() not in ("client", "customer"):
            return False

    # Do not auto-create for superusers or staff/admin
    if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
        return False

    # Don't create if already has a session as a customer
    if ChatSession.objects.filter(customer=user).exists():
        return False

    return True


@receiver(post_save, sender=User)
def auto_create_chat_session_for_user(sender, instance, created, **kwargs):
    """
    Automatically create a ChatSession for a new user, if applicable.
    This only creates a session if no ChatSession exists for this user as a customer.
    The agent may be left unassigned.
    """
    if not created or not ChatSession:
        return

    if should_create_for_user(instance):
        ChatSession.objects.create(customer=instance)


@receiver(post_migrate)
def auto_create_chat_session_for_existing_users(sender, **kwargs):
    """
    After migrations, ensure every appropriate user has a ChatSession.
    """
    if not ChatSession:
        return

    # You could optimize with .only() or .iterator() for large user tables
    for user in User.objects.all():
        if should_create_for_user(user):
            ChatSession.objects.create(customer=user)
