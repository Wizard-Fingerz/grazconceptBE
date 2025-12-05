import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from .models import StudyVisaApplicationComment, StudyVisaApplication
from .serializers import StudyVisaApplicationCommentSerializer
from account.client.models import Client

logger = logging.getLogger("visa.study.websocket")

class StudyVisaCommentConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time comments (chat-like) on StudyVisaApplication.
    Each application has its own "room", named by application id.
    Expects frontend to provide user_id with each action.
    """

    async def connect(self):
        """
        Called on incoming WebSocket connection request.
        Checks validity of the application_id, joins channel group, and accepts the connection.
        On error: closes the socket.
        """
        # Expect application_id provided in the URL, e.g. /ws/study/visa-application/<application_id>/
        try:
            self.application_id = self.scope['url_route']['kwargs'].get('application_id')
        except Exception as exc:
            logger.warning(f"Missing application_id in websocket scope: {exc}")
            await self.close(code=4001)
            return

        if not self.application_id:
            logger.warning("Application ID missing in websocket path")
            await self.close(code=4002)
            return

        # Defensive: ensure channel_layer is available
        if not hasattr(self, "channel_layer") or self.channel_layer is None:
            logger.error("No channel_layer in consumer. Check ASGI/Daphne/Channels config.")
            await self.close(code=4003)
            return

        self.room_group_name = f'Study_visa_application_{self.application_id}'

        try:
            application = await self._get_application(self.application_id)
        except Exception as exc:
            # file_context_0: Log "Application lookup error during connect:" with exc
            logger.warning(f"Application lookup error during connect: {exc}")
            await self.close(code=4004)
            return

        if application is None:
            logger.warning(f"Application with id {self.application_id} not found.")
            await self.close(code=4005)
            return

        self.application = application

        # Accept the connection early; user_id will be checked per message
        try:
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
        except Exception as exc:
            logger.error(f"Failed to join channel group {self.room_group_name}: {exc}")
            await self.close(code=4006)
            return

        await self.accept()
        response = {
            "type": "connection_successful",
            "message": "WebSocket connection established",
            "application_id": str(self.application_id),
        }
        await self.send_json(response)

    async def disconnect(self, close_code):
        # Try leaving group, but it's ok if errors happen on disconnect
        if getattr(self, "room_group_name", None):
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
        Receives and processes a message from the websocket.
        Expected format:
            {
              'action': 'send_comment',
              'text': 'comment text',
              'user_id': <user_id>,    # (required)
              'attachment': <optional>
            }
        """
        action = content.get("action")

        # Only support send_comment for now
        if action == "send_comment":
            text = (content.get("text") or "").strip()
            user_id = content.get("user_id")

            logger.info(f"Received request to create comment: user_id={user_id}, text={text!r}")

            if not user_id:
                await self.send_json({"error": "user_id must be provided."})
                return

            if not text:
                await self.send_json({"error": "Comment cannot be empty."})
                return

            # Lookup latest application every time, in case it changed or was deleted
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
            logger.info(f"Broadcasting comment message: {data}")

            # Broadcast to all group members
            try:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "comment_message",
                        "message": data,
                    }
                )
            except Exception as exc:
                logger.error(f"Error sending group message: {exc}")
                await self.send_json({"error": "Could not broadcast new comment."})
        else:
            await self.send_json({"error": "Unknown action: '%s'" % action})

    async def comment_message(self, event):
        """
        Handler for group messages (broadcast to all clients in the same group).
        """
        logger.info(f"Sending comment_message event to WebSocket: {event['message']}")
        await self.send_json(event["message"])

    @database_sync_to_async
    def _get_application(self, application_id):
        try:
            # 'applicant' is not a valid related field; use 'client'
            return StudyVisaApplication.objects.select_related("applicant").get(id=application_id)
        except StudyVisaApplication.DoesNotExist:
            return None

    @database_sync_to_async
    def _lookup_applicant_or_admin(self, user_id, application):
        """
        Return (applicant, admin) such that only one is not None.
        Only the correct application applicant (client) is allowed.
        """
        # Only allow commenting if user is the applicant for this application, or staff/admin in future
        try:
            # 'applicant' is not a field, should check against 'applicant_id'
            if application.applicant_id and str(application.applicant_id) == str(user_id):
                try:
                    applicant = Client.objects.get(id=user_id)
                    return (applicant, None)
                except Client.DoesNotExist:
                    return (None, None)
            # You may add admin-type support here later, if needed
            return (None, None)
        except Exception as exc:
            logger.warning(f"_lookup_applicant_or_admin error: {exc}")
            return (None, None)

    @database_sync_to_async
    def _create_comment(self, application, applicant, admin, text):
        try:
            return StudyVisaApplicationComment.objects.create(
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
        serializer = StudyVisaApplicationCommentSerializer(comment)
        return serializer.data
