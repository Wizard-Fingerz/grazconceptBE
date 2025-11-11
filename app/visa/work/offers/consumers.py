import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from .models import WorkVisaApplicationComment, WorkVisaApplication
from .serializers import WorkVisaApplicationCommentSerializer
from account.client.models import Client

logger = logging.getLogger("visa.work.websocket")

class WorkVisaCommentConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time comments (chat-like) on WorkVisaApplication.
    Each application has its own "room", named by application id.
    Instead of using Django's user in scope, expects frontend to provide user_id with each action.
    """

    async def connect(self):
        # Expect application_id provided in the URL, e.g. /ws/work/visa-application/<application_id>/
        self.application_id = self.scope['url_route']['kwargs'].get('application_id')
        # Defensive: check for missing application_id
        if not self.application_id:
            await self.close()
            return

        self.room_group_name = f'Work_visa_application_{self.application_id}'

        try:
            application = await self._get_application(self.application_id)
        except Exception as exc:
            logger.warning("Application lookup error: %s", exc)
            await self.close()
            return

        if application is None:
            await self.close()
            return

        self.application = application

        # Accept the connection early; user_id will be checked per message
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        response = {
            "type": "connection_successful",
            "message": "WebSocket connection established",
            "application_id": str(self.application_id),
        }
        await self.send_json(response)

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            try:
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )
            except Exception as exc:
                logger.warning(
                    f"Disconnect group_discard exception for application {getattr(self, 'application_id', None)}: {exc}"
                )

    async def receive_json(self, content):
        """
        Receive a message from websocket.
        Expected:
            {
              'action': 'send_comment',
              'text': 'comment text',
              'user_id': <user_id>,    # (required)
              'attachment': <optional>
            }
        """
        action = content.get("action")
        if action == "send_comment":
            text = (content.get("text") or "").strip()
            user_id = content.get("user_id")
            if not user_id:
                await self.send_json({"error": "user_id must be provided."})
                return

            if not text:
                await self.send_json({"error": "Comment cannot be empty."})
                return

            try:
                application = await self._get_application(self.application_id)
            except Exception as exc:
                logger.warning("Application lookup error in receive_json: %s", exc)
                await self.send_json({'error': "Application not found."})
                return

            if application is None:
                await self.send_json({'error': "Application not found."})
                return

            applicant, admin = await self._lookup_applicant_or_admin(user_id, application)
            if applicant is None and admin is None:
                await self.send_json({"error": "Not authorized."})
                return

            comment = await self._create_comment(application, applicant, admin, text)
            if comment is None:
                await self.send_json({"error": "Could not save comment."})
                return

            data = await self._serialize_comment(comment)
            data['action'] = "new_comment"
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "comment_message",
                    "message": data,
                }
            )
        else:
            await self.send_json({"error": "Unknown action"})

    async def comment_message(self, event):
        """Handler for group message send."""
        await self.send_json(event["message"])

    @database_sync_to_async
    def _get_application(self, application_id):
        try:
            return WorkVisaApplication.objects.select_related("applicant").get(id=application_id)
        except WorkVisaApplication.DoesNotExist:
            return None

    @database_sync_to_async
    def _lookup_applicant_or_admin(self, user_id, application):
        """
        Return (applicant, admin) such that only one is not None.
        Only the correct application.applicant is allowed.
        """
        try:
            if application.applicant_id and str(application.applicant_id) == str(user_id):
                try:
                    applicant = Client.objects.get(id=user_id)
                    return (applicant, None)
                except Client.DoesNotExist:
                    return (None, None)
            return (None, None)
        except Exception as exc:
            logger.warning(f"_lookup_applicant_or_admin error: {exc}")
            return (None, None)

    @database_sync_to_async
    def _create_comment(self, application, applicant, admin, text):
        try:
            return WorkVisaApplicationComment.objects.create(
                visa_application=application,
                applicant=applicant,
                admin=admin,
                text=text
            )
        except Exception as exc:
            logger.warning(f"Failed to create comment: {exc}")
            return None

    @database_sync_to_async
    def _serialize_comment(self, comment):
        serializer = WorkVisaApplicationCommentSerializer(comment)
        return serializer.data
