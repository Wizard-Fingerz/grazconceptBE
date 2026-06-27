from django.db import models
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password


class Wallet(models.Model):
    """
    Represents a user's wallet balance and status.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, related_name='wallet', on_delete=models.CASCADE
    )
    balance = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=10, default="NGN")
    is_active = models.BooleanField(default=True)

    # Transaction PIN - stored as a Django PBKDF2 hash. NULL means PIN not yet set.
    pin_hash = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user}'s Wallet: {self.balance} {self.currency}"

    # PIN helpers

    @property
    def has_pin(self):
        return bool(self.pin_hash)

    def set_pin(self, raw_pin):
        """Hash and persist a new 4-digit PIN."""
        self.pin_hash = make_password(raw_pin)
        self.save(update_fields=["pin_hash"])

    def verify_pin(self, raw_pin):
        """Return True if raw_pin matches the stored hash."""
        if not self.pin_hash:
            return False
        return check_password(raw_pin, self.pin_hash)
