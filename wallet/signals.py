
from django.db.models.signals import post_migrate
from django.apps import apps
from django.db.models.signals import post_save
from account.models import User
from django.dispatch import receiver

from .models import Wallet


@receiver(post_save, sender=User)
def create_wallet_for_user(sender, instance, created, **kwargs):
    """
    Signal to create a Wallet whenever a User is created.
    """
    if created:
        Wallet.objects.get_or_create(user=instance)


def create_wallets_for_users_without_wallets(sender, **kwargs):
    """
    Ensures all users have a wallet. Can be invoked via post_migrate signal
    or called manually.
    """
    User = apps.get_model('account', 'User')
    for user in User.objects.all():
        Wallet.objects.get_or_create(user=user)


post_migrate.connect(create_wallets_for_users_without_wallets)
