from django.db import models
from django.conf import settings

class Wallet(models.Model):
    """
    Represents a user's wallet balance and status.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='wallet', on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=10, default="NGN")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user}'s Wallet: {self.balance} {self.currency}"
