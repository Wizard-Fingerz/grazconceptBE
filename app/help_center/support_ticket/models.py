from django.db import models
from django.conf import settings

from definition.models import TableDropDownDefinition

def get_default_open_status():
    # Lazy import to avoid circular import issues
    # Assumes 'open' is the value of TableDropDownDefinition.code or similar field identifying open status
    return TableDropDownDefinition.objects.filter(
        table_name='support_ticket_status', term='Open'
    ).first()

class SupportTicket(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="support_tickets",
        on_delete=models.CASCADE,
        help_text="The user who created this ticket"
    )
    subject = models.CharField(max_length=80)
    status = models.ForeignKey(
        TableDropDownDefinition,
        on_delete=models.PROTECT,
        limit_choices_to={"table_name": "support_ticket_status"},
        help_text="The status of this ticket",
        default=get_default_open_status,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_reply = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Ticket #{self.pk}: {self.subject[:40]} ({self.status})"

    class Meta:
        ordering = ["-created_at"]

class SupportTicketMessage(models.Model):
    SENDER_USER = "user"
    SENDER_SUPPORT = "support"
    SENDER_CHOICES = [
        (SENDER_USER, "User"),
        (SENDER_SUPPORT, "Support"),
    ]

    ticket = models.ForeignKey(
        SupportTicket,
        related_name="messages",
        on_delete=models.CASCADE
    )
    sender = models.CharField(
        max_length=10,
        choices=SENDER_CHOICES,
        db_index=True
    )
    text = models.TextField(max_length=1000)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        who = "User" if self.sender == self.SENDER_USER else "Support"
        return f"{who} @ {self.timestamp}: {self.text[:60]}"

    class Meta:
        ordering = ["timestamp"]
