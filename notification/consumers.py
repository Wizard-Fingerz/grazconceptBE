import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        Accept only authenticated users, and join their personal notification group.
        Group name: "notifications_user_<user_id>"
        """
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
            return

        self.user_group_name = f'notifications_user_{user.id}'
        await self.channel_layer.group_add(self.user_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        """
        Leave the user's personal notification group on disconnect.
        """
        user = self.scope["user"]
        if not user.is_anonymous:
            await self.channel_layer.group_discard(f'notifications_user_{user.id}', self.channel_name)

    async def receive(self, text_data):
        """
        Optionally receive ping or mark all as read.
        """
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
            return

        data = json.loads(text_data)
        action = data.get("action")
        # Handle custom client actions if sent (e.g. mark all notifications as read)
        if action == "mark_all_as_read":
            await self.mark_all_as_read(user)
            await self.send(text_data=json.dumps({"status": "all_read"}))
        else:
            await self.send(text_data=json.dumps({'message': 'Connected to notifications socket!'}))

    @database_sync_to_async
    def mark_all_as_read(self, user):
        from .models import Notification
        Notification.objects.filter(user=user, is_read=False).update(is_read=True)

    async def send_notification(self, event):
        """
        Send notification event to the connected user.
        Event 'content' should be a dict representing the notification.
        """
        await self.send(text_data=json.dumps(event["content"]))
