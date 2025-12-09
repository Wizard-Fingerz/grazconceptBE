from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    # Call DRF's default exception handler first
    response = exception_handler(exc, context)

    # If DRF already handled it (ValidationError, PermissionDenied, etc.)
    if response is not None:
        return Response({
            "success": False,
            "message": response.data,
        }, status=response.status_code)

    # Log the actual error (for developers)
    request = context.get("request")
    view = context.get("view")

    logger.error(
        f"Unhandled Exception | View: {view} | Path: {request.path}",
        exc_info=True,
    )

    # Generic response to frontend
    return Response(
        {
            "success": False,
            "message": "Something went wrong. Please try again later."
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
