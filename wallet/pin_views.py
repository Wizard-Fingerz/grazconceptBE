"""
wallet/pin_views.py
-------------------
Endpoints for the wallet transaction PIN.

  GET  /wallet/pin/status/   -- { has_pin: true/false }
  POST /wallet/pin/setup/    -- create or change the PIN
  POST /wallet/pin/verify/   -- one-off check (used by bill pages before deducting wallet)
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status


def _get_wallet(user):
    try:
        return user.wallet
    except Exception:
        return None


class WalletPinStatusView(APIView):
    """GET /wallet/pin/status/ -> { "has_pin": true/false }"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        wallet = _get_wallet(request.user)
        if not wallet:
            return Response({"detail": "Wallet not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"has_pin": wallet.has_pin})


class WalletSetPinView(APIView):
    """
    POST /wallet/pin/setup/
    Body (first time):  { "pin": "1234", "confirm_pin": "1234" }
    Body (change):      { "current_pin": "1234", "pin": "5678", "confirm_pin": "5678" }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        pin         = (request.data.get("pin") or "").strip()
        confirm_pin = (request.data.get("confirm_pin") or "").strip()
        current_pin = (request.data.get("current_pin") or "").strip()

        if not pin.isdigit() or len(pin) != 4:
            return Response(
                {"detail": "PIN must be exactly 4 digits."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if pin != confirm_pin:
            return Response(
                {"detail": "PINs do not match."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        wallet = _get_wallet(request.user)
        if not wallet:
            return Response({"detail": "Wallet not found."}, status=status.HTTP_404_NOT_FOUND)

        # If a PIN already exists the user must supply it to change
        if wallet.has_pin:
            if not current_pin:
                return Response(
                    {"detail": "Your current PIN is required to set a new one."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not wallet.verify_pin(current_pin):
                return Response(
                    {"detail": "Current PIN is incorrect."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        wallet.set_pin(pin)
        return Response({"detail": "PIN set successfully.", "has_pin": True})


class WalletVerifyPinView(APIView):
    """
    POST /wallet/pin/verify/
    Body: { "pin": "1234" }
    Returns 200 if correct, 400 otherwise.
    Used by bill pages to gate wallet-deducting payments.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        pin = (request.data.get("pin") or "").strip()

        wallet = _get_wallet(request.user)
        if not wallet:
            return Response({"detail": "Wallet not found."}, status=status.HTTP_404_NOT_FOUND)

        if not wallet.has_pin:
            return Response(
                {"detail": "No PIN set. Please create your wallet PIN first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not wallet.verify_pin(pin):
            return Response(
                {"detail": "Incorrect PIN. Please try again."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"detail": "PIN verified."})
