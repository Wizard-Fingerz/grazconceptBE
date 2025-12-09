from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.core.exceptions import ValidationError as DjangoValidationError
import logging

logger = logging.getLogger(__name__)

def extract_validation_message(exc):
    """
    Normalize different ValidationError message formats
    into a clean response.
    """
    if hasattr(exc, "detail"):
        return exc.detail  # DRF ValidationError
    if hasattr(exc, "message_dict"):
        return exc.message_dict  # Django form/model ValidationError
    if hasattr(exc, "messages"):
        return exc.messages  # Django simple ValidationError
    return str(exc)


def custom_exception_handler(exc, context):
    # ✅ Let DRF handle known exceptions first
    response = exception_handler(exc, context)

    # ✅ Validation & business rule errors → exact message
    if response is not None:
        if isinstance(exc, (DRFValidationError, DjangoValidationError)):
            return Response(
                {
                    "success": False,
                    "message": extract_validation_message(exc),
                },
                status=response.status_code,
            )

        # ✅ Other DRF-handled errors (Auth, Permission, NotFound)
        return Response(
            {
                "success": False,
                "message": response.data,
            },
            status=response.status_code,
        )

    # ❌ Unknown / system errors → hide details
    request = context.get("request")
    view = context.get("view")

    logger.error(
        f"Unhandled Exception | View: {view} | Path: {request.path}",
        exc_info=True,
    )

    return Response(
        {
            "success": False,
            "message": "Something went wrong. Please try again later.",
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
