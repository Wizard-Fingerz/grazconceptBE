import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger("chat.websocket")

class ChatConsumer(AsyncWebsocketConsumer):
    """
    React-friendly ChatConsumer for customer <-> agent live chat.
    Accepts and responds to modern event-based commands in message payloads:
        command: 'send_message', 'get_messages', etc.

    Supports attachments, expected as base64-encoded content or as a URL/reference.
    """

    async def connect(self):
        """
        Accepts if proper chat_id & user_id in URL.
        """
        self.chat_id = self.scope['url_route']['kwargs'].get("chat_id", None)
        self.user_id = self.scope['url_route']['kwargs'].get("user_id", None)
        if not self.chat_id or not self.user_id:
            await self.close()
            return

        self.room_group_name = f"chat_{self.chat_id}"

        try:
            self.chat_session = await self.get_chat_session(self.chat_id)
        except Exception as exc:
            logger.warning("Invalid chat_session: %s", exc)
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Send a successful connection message to the frontend
        response = {
            "type": "connection_successful",
            "message": "WebSocket connection established",
            "chat_id": str(self.chat_id),
            "user_id": str(self.user_id),
        }
        print("BACKEND RESPONSE:", response)
        await self.send(text_data=json.dumps(response))

        # Optionally send message history on connect
        await self.send_history()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """
        Accepts commands:
            - {command: 'send_message', message: "...", attachment: ...}
            - {command: 'get_messages'}
        """
        try:
            data = json.loads(text_data)
        except Exception:
            response = {"error": "Invalid JSON"}
            print("BACKEND RESPONSE:", response)
            await self.send(text_data=json.dumps(response))
            return

        command = data.get("command", None)
        if command == "send_message":
            await self.handle_send_message(data)
        elif command == "get_messages":
            await self.send_history()
        else:
            # Default: backwards compatibility for simple text send
            # (for legacy clients not using explicit 'command')
            if "message" in data or "attachment" in data:
                await self.handle_send_message(data)
            else:
                response = {"error": "Unknown command"}
                print("BACKEND RESPONSE:", response)
                await self.send(text_data=json.dumps(response))

    async def handle_send_message(self, data):
        msg = data.get("message", "")
        attachment = data.get("attachment", None)

        # --- Root cause analysis and fix for "{'message': 'hi'}" issue ---
        # Sometimes, the frontend may wrongly encode JSON messages as a string representing a dict,
        # or double-encode the object so that 'msg' is actually a dict or a JSON string that is itself a serialized dict.

        # Defensive check: If message is a dict, extract 'message' field (common React/JS bug).
        # If message is a JSON string like "{'message':'hi'}", try to parse it.
        # Root cause: ChatConsumer.handle_send_message() is storing a non-str into Message.message,
        # either a dict directly or a JSON-stringified dict,
        # when only the plain text is expected. This results in str(dict) stored, which
        # becomes "'message': 'hi'", and that's why you receive 'message': "{'message': 'hi'}".

        # --- Defensive cleanup for incoming msg ---
        # If 'msg' is a dict, try to extract a text string
        if isinstance(msg, dict):
            # Likely coming from a buggy frontend sending e.g. {message: {message:'hi'}}
            msg = msg.get('message', str(msg))
        elif isinstance(msg, str):
            # Sometimes JavaScript can send a JSON-stringified dict as the message
            # Try to detect and parse it safely
            try:
                # Try parsing string as JSON if it looks like a JSON object
                if msg.strip().startswith("{") and msg.strip().endswith("}"):
                    possible_dict = json.loads(msg.replace("'", '"'))
                    if isinstance(possible_dict, dict) and 'message' in possible_dict:
                        msg = possible_dict['message']
            except Exception:
                # Ignore if parsing fails; just use as is
                pass

        # Now msg should be just a string
        if not isinstance(msg, str):
            msg = str(msg)

        sender_id = int(self.user_id)
        chat_session = self.chat_session
        if sender_id == chat_session.customer_id:
            sender_type = "customer"
            recipient_id = chat_session.agent_id
        elif sender_id == chat_session.agent_id:
            sender_type = "agent"
            recipient_id = chat_session.customer_id
        else:
            response = {"error": "Unauthorized"}
            print("BACKEND RESPONSE:", response)
            await self.send(text_data=json.dumps(response))
            return

        message_obj = await self.create_message(
            chat_session,
            sender_id,
            recipient_id,
            sender_type,
            msg,
            attachment
        )

        # Important: Do not combine message and attachment together in returned message_data!
        message_data = await self.message_to_dict(message_obj)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message_data,
            }
        )

    async def send_history(self):
        """
        Send full message history to the client (for get_messages or on connect).
        """
        messages_data = await self.get_message_history(self.chat_id)
        response = {
            "type": "history",
            "messages": messages_data,
        }
        print("BACKEND RESPONSE:", response)
        await self.send(text_data=json.dumps(response))

    async def chat_message(self, event):
        """
        Send new incoming message to websocket client.
        """
        response = {
            "type": "message",
            "message": event["message"]
        }
        print("BACKEND RESPONSE:", response)
        await self.send(text_data=json.dumps(response))

    @database_sync_to_async
    def get_chat_session(self, chat_id):
        from chat.models import ChatSession
        try:
            return ChatSession.objects.select_related("customer", "agent").get(id=chat_id)
        except ChatSession.DoesNotExist:
            # If the session does not exist, raise so connect will close the ws
            raise

    @database_sync_to_async
    def get_message_history(self, chat_id):
        from chat.models import Message
        # Query the most recent 50 messages, if none exist returns empty list
        qs = Message.objects.filter(chat_session_id=chat_id).select_related("sender", "recipient").order_by("-timestamp")[:50]
        return [self.serialize_message(msg) for msg in reversed(list(qs))]

    @database_sync_to_async
    def create_message(self, chat_session, sender_id, recipient_id, sender_type, text, attachment):
        from django.contrib.auth import get_user_model
        from chat.models import Message
        User = get_user_model()
        sender = User.objects.get(pk=sender_id)
        recipient = User.objects.get(pk=recipient_id)
        # Defensive: guarantee 'message' is only a string (database model expects text)
        if not isinstance(text, str):
            text = str(text)
        msg_kwargs = dict(
            chat_session=chat_session,
            sender=sender,
            recipient=recipient,
            sender_type=sender_type,
            message=text
        )
        if attachment:
            if isinstance(attachment, str):
                if attachment.strip() != "":
                    msg_kwargs['attachment'] = attachment
            else:
                msg_kwargs['attachment'] = attachment
        return Message.objects.create(**msg_kwargs)

    @database_sync_to_async
    def message_to_dict(self, message):
        return self.serialize_message(message)

    def serialize_message(self, msg):
        # The message should not contain the attachment as part of the message content!
        # Only the "attachment" field should contain file/url/base64 reference, and "message" should be text only.
        attachment_url = None
        if getattr(msg, "attachment", None):
            try:
                # If using FileField, use .url if available (uploaded files)
                if hasattr(msg.attachment, "url"):
                    attachment_url = msg.attachment.url
                else:
                    attachment_url = str(msg.attachment)
            except Exception:
                attachment_url = str(msg.attachment)
        # Ensure the message value is proper string (not a dict as seen in error)
        cleaned_message = msg.message
        if isinstance(cleaned_message, dict):
            # Defensive: Should never happen now due to input checks, but clean anyway
            cleaned_message = cleaned_message.get('message', '') if 'message' in cleaned_message else str(cleaned_message)
        elif not isinstance(cleaned_message, str):
            cleaned_message = str(cleaned_message)
        return {
            "id": msg.id,
            "chat_id": str(msg.chat_session_id),
            "sender_id": msg.sender_id,
            "sender_name": getattr(msg.sender, "full_name", str(msg.sender)),
            "sender_type": msg.sender_type,
            "message": cleaned_message,  # ensure text only, no dict/JSON
            "timestamp": msg.timestamp.isoformat(),
            "read": msg.read,
            "attachment": attachment_url,  # File url, string, or None.
        }


class ChatSessionListConsumer(AsyncWebsocketConsumer):
    """
    React-friendly consumer for listing a user's chat sessions and event updates.
    Accepts event-style commands:
      - {command: 'sessions_list'}       -> emits type: 'chats'
      - {command: 'refresh'} or legacy   -> also emits type: 'chats'
    """

    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs'].get("user_id", None)
        if not self.user_id:
            await self.close()
            return

        self.room_group_name = f"user_chats_{self.user_id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        # Send a successful connection message to the frontend
        response = {
            "type": "connection_successful",
            "message": "WebSocket connection established",
            "user_id": str(self.user_id),
        }
        await self.send(text_data=json.dumps(response))
        await self.send_sessions_list()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """
        Accepts event requests for sessions_list, etc.
        """
        try:
            data = json.loads(text_data)
        except Exception:
            response = {"error": "Invalid JSON"}
            print("BACKEND RESPONSE:", response)
            await self.send(text_data=json.dumps(response))
            return

        cmd = data.get("command")
        if cmd in ("refresh", "sessions_list"):
            await self.send_sessions_list()
        else:
            response = {"error": "Unknown command"}
            print("BACKEND RESPONSE:", response)
            await self.send(text_data=json.dumps(response))

    async def send_sessions_list(self):
        sessions = await self.get_user_chat_sessions(self.user_id)
        response = {
            "type": "chats",
            "sessions": sessions,
        }
        print("BACKEND RESPONSE:", response)
        await self.send(text_data=json.dumps(response))

    async def chat_session_update(self, event):
        """
        Broadcasts a change to a chat session (status/message/unread/etc).
        """
        session = event.get("session")
        response = {
            "type": "chat_update",
            "session": session,
        }
        print("BACKEND RESPONSE:", response)
        await self.send(text_data=json.dumps(response))

    @database_sync_to_async
    def get_user_chat_sessions(self, user_id):
        from django.contrib.auth import get_user_model
        from chat.models import ChatSession
        from django.db import models

        User = get_user_model()
        qs = ChatSession.objects.filter(
            models.Q(customer_id=user_id) | models.Q(agent_id=user_id)
        ).select_related("agent", "customer")
        result = []
        for sess in qs:
            agent_name = getattr(sess.agent, "full_name", "Unassigned") if sess.agent else "Unassigned"
            last_msg_dt = sess.last_message_at()
            try:
                unread_count = sess.unread_count_for_user(User.objects.get(pk=user_id))
            except Exception:
                unread_count = 0
            result.append({
                "id": str(sess.id),
                "agent_id": sess.agent_id,
                "agent_name": agent_name,
                "status": sess.status,
                "priority": sess.priority,
                "service_title": sess.service_title,
                "last_message_at": last_msg_dt.isoformat() if last_msg_dt else "",
                "unread_count": unread_count,
            })
        # No sessions? Result is still an empty list, which is serializable.
        result.sort(key=lambda s: (s["status"] != "active", -(s["unread_count"]), s["last_message_at"]), reverse=False)
        return result

