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
    Also, if the user was created_by another user, create a session between them.
    """
    if not created or not ChatSession:
        return

    chat_sessions_created = set()

    # 1. If eligible customer: create with every admin
    if should_create_for_user(instance):
        admins = get_all_admins().distinct()
        if admins.exists():
            for admin in admins:
                if not ChatSession.objects.filter(customer=instance, agent=admin).exists():
                    ChatSession.objects.create(customer=instance, agent=admin)
                    chat_sessions_created.add(('admin', admin.pk))
        else:
            # Fallback: create a session with no agent if no admins are present
            if not ChatSession.objects.filter(customer=instance, agent=None).exists():
                ChatSession.objects.create(customer=instance, agent=None)
                chat_sessions_created.add(('noadmin', None))

    # 2. If created_by is set (regardless of client/user type): create session with creator as agent if not already created above
    creator = getattr(instance, 'created_by', None)
    if creator and creator != instance:
        already = ChatSession.objects.filter(customer=instance, agent=creator).exists()
        if not already:
            ChatSession.objects.create(customer=instance, agent=creator)


@receiver(post_migrate)
def auto_create_chat_sessions_for_existing_users(sender, **kwargs):
    """
    After migrations, ensure every eligible customer has a ChatSession
    with every admin.
    Also ensure any user with created_by has a session with their creator.
    """
    if not ChatSession:
        return

    admins = get_all_admins().distinct()
    for user in User.objects.all():
        created_sessions = set()

        # 1. For eligible customer: ChatSession with every admin
        if should_create_for_user(user):
            if admins.exists():
                for admin in admins:
                    if not ChatSession.objects.filter(customer=user, agent=admin).exists():
                        ChatSession.objects.create(customer=user, agent=admin)
                        created_sessions.add(('admin', admin.pk))
            else:
                # Fallback: create a session with no agent if no admins are present
                if not ChatSession.objects.filter(customer=user, agent=None).exists():
                    ChatSession.objects.create(customer=user, agent=None)
                    created_sessions.add(('noadmin', None))

        # 2. If user has a creator, create a (customer=user, agent=creator) session if not exists
        creator = getattr(user, 'created_by', None)
        if creator and creator != user:
            already = ChatSession.objects.filter(customer=user, agent=creator).exists()
            if not already:
                ChatSession.objects.create(customer=user, agent=creator)
