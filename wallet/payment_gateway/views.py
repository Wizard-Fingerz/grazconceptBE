import json
import logging

from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from wallet.models import Wallet
from wallet.transactions.models import WalletTransaction
from .models import PaymentGateway, PaymentGatewayCallbackLog
from .serializers import PaymentGatewaySerializer, PaymentGatewayCallbackLogSerializer
from . import flutterwave_service as flw

logger = logging.getLogger(__name__)


# ─── Admin CRUD viewsets (unchanged) ──────────────────────────────────────────

class PaymentGatewayViewSet(viewsets.ModelViewSet):
    queryset = PaymentGateway.objects.all()
    serializer_class = PaymentGatewaySerializer
    permission_classes = [permissions.IsAuthenticated]


class PaymentGatewayCallbackLogViewSet(viewsets.ModelViewSet):
    queryset = PaymentGatewayCallbackLog.objects.all()
    serializer_class = PaymentGatewayCallbackLogSerializer
    permission_classes = [permissions.IsAuthenticated]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_or_create_flw_gateway():
    gw, _ = PaymentGateway.objects.get_or_create(
        name="flutterwave",
        defaults={"is_active": True, "credentials": {"public_key": settings.FLUTTERWAVE_PUBLIC_KEY}},
    )
    return gw


def _get_wallet(user):
    try:
        return Wallet.objects.get(user=user)
    except Wallet.DoesNotExist:
        return None


# ─── 1. Initiate payment (deposit) ────────────────────────────────────────────

class FlutterwaveInitiateView(APIView):
    """
    POST /wallet/flutterwave/initiate/
    Body: { "amount": 5000, "currency": "NGN", "transaction_type": "deposit",
            "description": "Wallet top-up", "savings_plan_id": null }

    Returns: { "reference": "GC-xxx", "public_key": "FLWPUBK_...", "amount": 5000, ... }
    The frontend uses these to open the Flutterwave inline checkout.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        amount = request.data.get("amount")
        currency = request.data.get("currency", "NGN")
        tx_type = request.data.get("transaction_type", "deposit")
        description = request.data.get("description", "Wallet transaction")
        savings_plan_id = request.data.get("savings_plan_id")

        if not amount:
            return Response({"detail": "Amount is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return Response({"detail": "Amount must be a positive number."}, status=status.HTTP_400_BAD_REQUEST)

        wallet = _get_wallet(request.user)
        if not wallet:
            return Response({"detail": "Wallet not found."}, status=status.HTTP_404_NOT_FOUND)

        # For non-deposit ops, ensure sufficient balance
        if tx_type != "deposit":
            if float(wallet.balance) < amount:
                return Response({"detail": "Insufficient wallet balance."}, status=status.HTTP_400_BAD_REQUEST)

        reference = flw.generate_reference("GC")

        # Create a pending transaction record
        gateway = _get_or_create_flw_gateway()
        kwargs = dict(
            user=request.user,
            wallet=wallet,
            transaction_type=tx_type,
            amount=amount,
            currency=currency,
            status="pending",
            reference=reference,
            payment_gateway=gateway,
            description=description,
        )
        if savings_plan_id:
            from wallet.saving_plans.models import SavingsPlan
            try:
                kwargs["savings_plan"] = SavingsPlan.objects.get(pk=savings_plan_id, user=request.user)
            except SavingsPlan.DoesNotExist:
                pass

        WalletTransaction.objects.create(**kwargs)

        return Response({
            "reference": reference,
            "public_key": settings.FLUTTERWAVE_PUBLIC_KEY,
            "amount": amount,
            "currency": currency,
            "email": request.user.email,
            "name": f"{request.user.first_name} {request.user.last_name}".strip() or request.user.email,
            "phone": getattr(request.user, "phone_number", "") or "",
            "transaction_type": tx_type,
            "description": description,
        }, status=status.HTTP_200_OK)


# ─── 2. Verify payment (after inline checkout) ────────────────────────────────

class FlutterwaveVerifyView(APIView):
    """
    POST /wallet/flutterwave/verify/
    Body: { "transaction_id": 12345678, "reference": "GC-xxx" }

    Verifies the payment with Flutterwave and updates the wallet transaction.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        flw_tx_id = request.data.get("transaction_id")
        reference = request.data.get("reference")

        if not flw_tx_id or not reference:
            return Response({"detail": "transaction_id and reference are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Look up our pending transaction
        try:
            tx = WalletTransaction.objects.get(reference=reference, user=request.user)
        except WalletTransaction.DoesNotExist:
            return Response({"detail": "Transaction not found."}, status=status.HTTP_404_NOT_FOUND)

        if tx.status == "successful":
            return Response({"detail": "Transaction already verified.", "status": "successful"})

        # Call Flutterwave
        try:
            flw_data = flw.verify_payment(int(flw_tx_id))
        except Exception as exc:
            tx.status = "failed"
            tx.meta = {"error": str(exc)}
            tx.save(update_fields=["status", "meta"])
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        # Validate amount + currency match
        paid_amount = float(flw_data.get("amount", 0))
        paid_currency = flw_data.get("currency", "")
        flw_status = flw_data.get("status", "")

        if flw_status != "successful":
            tx.status = "failed"
            tx.meta = flw_data
            tx.save(update_fields=["status", "meta"])
            return Response({"detail": "Payment was not successful."}, status=status.HTTP_400_BAD_REQUEST)

        if paid_currency != tx.currency or abs(paid_amount - float(tx.amount)) > 1:
            tx.status = "failed"
            tx.meta = {"error": "Amount/currency mismatch", "flw_data": flw_data}
            tx.save(update_fields=["status", "meta"])
            return Response({"detail": "Payment amount or currency mismatch."}, status=status.HTTP_400_BAD_REQUEST)

        # Mark successful — the model's save() auto-processes balance
        tx.status = "successful"
        tx.meta = flw_data
        tx.save(update_fields=["status", "meta"])

        return Response({
            "detail": "Payment verified successfully.",
            "status": "successful",
            "reference": reference,
            "amount": paid_amount,
            "currency": paid_currency,
            "new_balance": float(tx.wallet.balance),
        })


# ─── 3. Webhook ───────────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name="dispatch")
class FlutterwaveWebhookView(APIView):
    """
    POST /wallet/flutterwave/webhook/
    Receives Flutterwave webhook events (charge.completed, transfer.completed).
    Validates the verif-hash header.
    """
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        received_hash = request.headers.get("verif-hash", "")
        if not flw.validate_webhook_signature(request.body, received_hash):
            logger.warning("Flutterwave webhook: invalid signature")
            return Response({"detail": "Invalid signature."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return Response({"detail": "Invalid JSON."}, status=status.HTTP_400_BAD_REQUEST)

        event = payload.get("event", "")
        data = payload.get("data", {})

        gateway = _get_or_create_flw_gateway()

        # Log every webhook
        log = PaymentGatewayCallbackLog.objects.create(
            payment_gateway=gateway,
            payload=payload,
            processed=False,
        )

        if event == "charge.completed":
            self._handle_charge(data, log)
        elif event in ("transfer.completed", "transfer.failed"):
            self._handle_transfer(data, log)

        log.processed = True
        log.save(update_fields=["processed"])
        return Response({"status": "ok"})

    def _handle_charge(self, data: dict, log):
        ref = data.get("tx_ref") or data.get("txRef")
        flw_status = data.get("status", "")
        if not ref:
            return
        try:
            tx = WalletTransaction.objects.get(reference=ref)
        except WalletTransaction.DoesNotExist:
            return

        log.wallet_transaction = tx
        if flw_status == "successful" and tx.status != "successful":
            tx.status = "successful"
            tx.meta = data
            tx.save(update_fields=["status", "meta"])
        elif flw_status == "failed" and tx.status == "pending":
            tx.status = "failed"
            tx.meta = data
            tx.save(update_fields=["status", "meta"])

    def _handle_transfer(self, data: dict, log):
        ref = data.get("reference")
        flw_status = data.get("status", "")
        if not ref:
            return
        try:
            tx = WalletTransaction.objects.get(reference=ref)
        except WalletTransaction.DoesNotExist:
            return

        log.wallet_transaction = tx
        if flw_status in ("SUCCESSFUL", "successful") and tx.status != "successful":
            tx.status = "successful"
            tx.meta = data
            tx.save(update_fields=["status", "meta"])
        elif flw_status in ("FAILED", "failed") and tx.status == "pending":
            tx.status = "failed"
            tx.meta = data
            tx.save(update_fields=["status", "meta"])


# ─── 4. Withdrawal (bank transfer) ────────────────────────────────────────────

class FlutterwaveWithdrawView(APIView):
    """
    POST /wallet/flutterwave/withdraw/
    Body: { "amount": 5000, "account_bank": "044", "account_number": "0123456789",
            "beneficiary_name": "John Doe", "narration": "Wallet withdrawal",
            "currency": "NGN" }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        amount = request.data.get("amount")
        account_bank = request.data.get("account_bank")
        account_number = request.data.get("account_number")
        beneficiary_name = request.data.get("beneficiary_name", "")
        narration = request.data.get("narration", "Wallet withdrawal")
        currency = request.data.get("currency", "NGN")

        if not all([amount, account_bank, account_number]):
            return Response({"detail": "amount, account_bank, and account_number are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return Response({"detail": "Amount must be a positive number."}, status=status.HTTP_400_BAD_REQUEST)

        wallet = _get_wallet(request.user)
        if not wallet:
            return Response({"detail": "Wallet not found."}, status=status.HTTP_404_NOT_FOUND)
        if float(wallet.balance) < amount:
            return Response({"detail": "Insufficient wallet balance."}, status=status.HTTP_400_BAD_REQUEST)

        reference = flw.generate_reference("GCW")
        gateway = _get_or_create_flw_gateway()

        # Pre-create transaction as pending (balance debited only on success via signal/save)
        tx = WalletTransaction.objects.create(
            user=request.user,
            wallet=wallet,
            transaction_type="withdrawal",
            amount=amount,
            currency=currency,
            status="pending",
            reference=reference,
            payment_gateway=gateway,
            description=narration,
        )

        try:
            flw_data = flw.initiate_transfer(
                account_bank=account_bank,
                account_number=account_number,
                amount=amount,
                narration=narration,
                currency=currency,
                reference=reference,
                beneficiary_name=beneficiary_name,
            )
            tx.meta = flw_data
            tx.save(update_fields=["meta"])
        except Exception as exc:
            tx.status = "failed"
            tx.meta = {"error": str(exc)}
            tx.save(update_fields=["status", "meta"])
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "detail": "Withdrawal initiated. Funds will be sent to your account shortly.",
            "reference": reference,
            "status": "pending",
            "amount": amount,
            "currency": currency,
        })


# ─── 5. Banks list ────────────────────────────────────────────────────────────

class FlutterwaveBanksView(APIView):
    """GET /wallet/flutterwave/banks/?country=NG"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        country = request.query_params.get("country", "NG")
        try:
            banks = flw.get_banks(country)
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"banks": banks})


# ─── 6. Account name resolution ───────────────────────────────────────────────

class FlutterwaveResolveAccountView(APIView):
    """
    POST /wallet/flutterwave/resolve-account/
    Body: { "account_number": "0123456789", "account_bank": "044" }
    Returns: { "account_name": "JOHN DOE", "account_number": "0123456789" }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        account_number = (request.data.get("account_number") or "").strip()
        account_bank   = (request.data.get("account_bank")   or "").strip()

        if not account_number or not account_bank:
            return Response(
                {"detail": "account_number and account_bank are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(account_number) != 10 or not account_number.isdigit():
            return Response(
                {"detail": "account_number must be exactly 10 digits."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            data = flw.resolve_account(account_number, account_bank)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.exception("resolve_account error: %s", exc)
            return Response(
                {"detail": "Account lookup failed. Please try again."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({
            "account_name":   data.get("account_name", ""),
            "account_number": data.get("account_number", account_number),
        })
