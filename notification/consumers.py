import json
import logging
from urllib.parse import parse_qs
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

Notification = None
NotificationSerializer = None

logger = logging.getLogger("notification.websocket")

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        Accepts a websocket connection if 'user_id' provided and user has notifications.
        Response is always built in this async context safely.
        """
        try:
            user_id = self._get_user_id_from_query()
            if user_id is not None:
                notifications_data = await self.get_notifications_data_for_user_id(user_id)
                if notifications_data:
                    await self.accept()
                    await self.send(text_data=json.dumps({
                        "message": "Connected to notifications socket!",
                        "notifications": notifications_data
                    }))
                else:
                    logger.info("No notifications found for user_id=%r. Closing connection.", user_id)
                    await self.close()
            else:
                logger.info("No user_id provided in query string. Closing connection.")
                await self.close()
        except Exception as exc:
            logger.exception("WebSocket connection error: %s", exc)
            # Use only valid close code (1000 for normal closure)
            await self.close(code=1000)

    async def disconnect(self, close_code):
        logger.info("WebSocket disconnected with code: %s", close_code)

    async def receive(self, text_data):
        user_id = self._get_user_id_from_query()
        if not user_id:
            logger.info("Received data but no user_id in query string: %s", text_data)
            await self.send(text_data=json.dumps({'error': 'user_id required in query string.'}))
            await self.close()
            return
        notifications_data = await self.get_notifications_data_for_user_id(user_id)
        await self.send(text_data=json.dumps({'notifications': notifications_data}))

    @database_sync_to_async
    def get_notifications_for_user_id(self, user_id):
        """
        Fetches notifications queryset, up to ten, most recent first.
        """
        NotificationModel = self.get_notification_model()
        try:
            notifications = NotificationModel.objects.filter(user_id=user_id).order_by('-created_at')[:10]
            return list(notifications)
        except Exception as e:
            logger.debug("Notification query failed for user_id=%r: %s", user_id, e)
            return []

    @database_sync_to_async
    def get_notifications_data_for_user_id(self, user_id):
        """
        Gets serialized notification data for given user_id, handling ORM/serializer in sync context.
        """
        NotificationModel = self.get_notification_model()
        Serializer = self.get_notification_serializer()
        try:
            notifications = NotificationModel.objects.filter(user_id=user_id).order_by('-created_at')[:10]
            serializer = Serializer(notifications, many=True)
            return serializer.data
        except Exception as e:
            logger.debug("Failed to fetch/serialize notifications for user_id=%r: %s", user_id, e)
            return []

    async def send_notification(self, event):
        user_id = self._get_user_id_from_query()
        notification_data = event.get("content", {})
        notif_user_id = str(notification_data.get("user"))
        if user_id and str(user_id) == notif_user_id:
            await self.send(text_data=json.dumps(notification_data))
        else:
            logger.debug(
                "Attempted to send notification for user %s, but connection user_id was %s",
                notif_user_id, user_id
            )

    def _get_user_id_from_query(self):
        query_string = self.scope.get("query_string", b"").decode("utf8")
        params = parse_qs(query_string)
        user_id_list = params.get("user_id", [])
        if user_id_list:
            return user_id_list[0]
        return None

    def get_notification_model(self):
        global Notification
        if Notification is None:
            from .models import Notification as Notif
            Notification = Notif
        return Notification

    def get_notification_serializer(self):
        global NotificationSerializer
        if NotificationSerializer is None:
            from .serializers import NotificationSerializer as NotifSerializer
            NotificationSerializer = NotifSerializer
        return NotificationSerializer
