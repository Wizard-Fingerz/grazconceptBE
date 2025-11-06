from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatSession(models.Model):
    """
    Represents a chat session between a customer/client (who inherits from User)
    and their assigned Agent (also a User, usually with a specific user_type/role).
    """
    # Customer or client user
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_sessions',
        help_text="The client/user who is chatting with their agent.",
    )
    # Agent user (generally an internal staff, distinguished by user_type/role)
    agent = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_chats_as_agent',
        help_text="The agent assigned to this session.",
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('resolved', 'Resolved'),
            ('closed', 'Closed'),
        ],
        default='active',
        help_text="The current status of the chat session.",
    )
    priority = models.CharField(
        max_length=20,
        choices=[
            ('urgent', 'Urgent'),
            ('high', 'High'),
            ('medium', 'Medium'),
            ('low', 'Low'),
        ],
        default='medium',
        help_text="Session resolution priority.",
    )
    service_title = models.CharField(
        max_length=255,
        blank=True,
        help_text="Short title describing the reason/purpose, e.g. 'Document Upload Help'."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def unread_count_for_user(self, user):
        return self.messages.filter(recipient=user, read=False).count()

    def last_message_at(self):
        last_msg = self.messages.order_by('-timestamp').first()
        return last_msg.timestamp if last_msg else self.created_at

    def __str__(self):
        return f"ChatSession #{self.id} ({self.customer.full_name} ⇄ {self.agent.full_name if self.agent else 'Unassigned'})"


class Message(models.Model):
    """
    A message within a chat session.
    Only the customer (client) and assigned agent can be sender or recipient.
    """
    chat_session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_chat_messages'
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_chat_messages',
        help_text="The user receiving this message (either agent or customer)."
    )
    sender_type = models.CharField(
        max_length=20,
        choices=[('customer', 'Customer'), ('agent', 'Agent')],
        help_text="Whether the sender is a customer or agent."
    )
    message = models.TextField(blank=True)
    attachment = models.FileField(upload_to='chat_media/', blank=True, null=True)
    # You can extend to support attachments if needed later
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message #{self.id} by {self.sender.full_name} to {self.recipient.full_name} in ChatSession #{self.chat_session_id}"

    class Meta:
        ordering = ['timestamp']
