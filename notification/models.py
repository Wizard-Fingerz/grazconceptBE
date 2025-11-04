from django.db import models
from django.conf import settings

class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = (
        ("wallet", "Wallet"),
        ("transaction", "Transaction"),
        ("savings", "Savings"),
        ("system", "System"),
        ("promo", "Promotion"),
        ("other", "Other"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="notifications",
        on_delete=models.CASCADE,
        help_text="The user to whom this notification belongs",
    )
    title = models.CharField(
        max_length=200,
        help_text="Title or short heading for the notification."
    )
    message = models.TextField(
        help_text="Notification message body."
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPE_CHOICES,
        default="other",
        help_text="Type/category of notification."
    )
    data = models.JSONField(
        blank=True,
        null=True,
        help_text="Optional extra context or metadata (e.g. transaction id, reference)."
    )
    is_read = models.BooleanField(
        default=False,
        help_text="Whether the notification has been read by the user."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the notification was created."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When the notification was last updated."
    )

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])

    def __str__(self):
        return f"Notification to {self.user}: {self.title[:40]} {'(read)' if self.is_read else '(unread)'}"

    class Meta:
        ordering = ["-created_at"]

