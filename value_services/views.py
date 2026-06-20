"""
Value-services bill payment views.
Endpoints:
  POST /api/value-services/bills/pay/          → electricity
  POST /api/value-services/cable-internet/renew/ → cable TV / internet
  POST /api/value-services/education-fees/pay/  → education / exam fees
  POST /api/value-services/webhook/flutterwave/ → Flutterwave payment webhook
"""
import logging
from decimal import Decimal
from django.utils import timezone
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CableTVSubscription, BillPaymentRecord
from .serializers import (
    ElectricityPayRequestSerializer,
    CableRenewRequestSerializer,
    EducationFeePayRequestSerializer,
)
from . import services

logger = logging.getLogger(__name__)


# ── Shared payment dispatcher ────────────────────────────────────────────────

def _get_redirect_url():
    frontend = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
    return f"{frontend}/services/bills?payment=success"


def _build_flutterwave_meta_for_record(record_type: str, record_id: int, **extra):
    return {"record_type": record_type, "record_id": record_id, **extra}


def _execute_electricity(record: BillPaymentRecord):
    """Call PremiumSub for electricity and update record."""
    p = record.payload
    result = services.purchase_electricity(
        provider=p["provider"],
        meter_type=p["meter_type"],
        meter_number=p["meter_number"],
        amount=record.amount,
        reference=record.transaction_reference,
    )
    record.provider_reference = result["provider_reference"]
    record.token = result.get("token", "")
    record.meta["raw_response"] = str(result.get("raw_response", {}))
    record.status = "successful"
    record.completed_at = timezone.now()
    record.save()


def _execute_cable(subscription: CableTVSubscription):
    """Call PremiumSub for cable/internet and update record."""
    result = services.renew_cable_subscription(
        provider=subscription.provider,
        iuc_number=subscription.iuc_number,
        package_code=subscription.package_code,
        amount=subscription.amount,
        reference=subscription.transaction_reference,
    )
    subscription.provider_reference = result["provider_reference"]
    subscription.meta["raw_response"] = str(result.get("raw_response", {}))
    subscription.status = "successful"
    subscription.completed_at = timezone.now()
    subscription.save()


def _execute_education(record: BillPaymentRecord):
    """Call PremiumSub for education and update record."""
    p = record.payload
    result = services.purchase_education_pin(
        provider=p["provider"],
        fee_type=p["fee_type"],
        amount=record.amount,
        reference=record.transaction_reference,
        candidate_name=p.get("candidate_name", ""),
        reg_no=p.get("reg_no", ""),
    )
    record.provider_reference = result["provider_reference"]
    record.token = result.get("token", "")
    record.meta["raw_response"] = str(result.get("raw_response", {}))
    record.status = "successful"
    record.completed_at = timezone.now()
    record.save()


# ── Electricity ───────────────────────────────────────────────────────────────

class ElectricityBillPayView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = ElectricityPayRequestSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        data = ser.validated_data
        user = request.user
        amount = Decimal(str(data["amount"]))
        payment_method = data["payment_method"]
        ref = services.generate_reference("EL")
        flw_tx_ref = services.generate_reference("FLW-EL")

        # Create pending record
        record = BillPaymentRecord.objects.create(
            user=user,
            bill_type="electricity",
            payment_method=payment_method,
            status="pending",
            amount=amount,
            transaction_reference=ref,
            flw_tx_ref=flw_tx_ref if payment_method != "wallet" else "",
            payload={
                "provider": data["provider"],
                "meter_type": data["meter_type"],
                "meter_number": data["meter_number"],
            },
        )

        if payment_method == "wallet":
            # Synchronous: debit wallet → call API
            try:
                services.debit_wallet(
                    user=user,
                    amount=amount,
                    description=f"Electricity bill — {data['provider']} meter {data['meter_number']}",
                    reference=ref,
                    meta={"bill_payment_id": record.id},
                )
            except ValueError as e:
                record.status = "failed"
                record.error_message = str(e)
                record.save()
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            try:
                _execute_electricity(record)
            except ValueError as e:
                # Refund wallet on API failure
                services.refund_wallet(
                    user=user,
                    amount=amount,
                    description=f"Refund: electricity bill failed — {data['provider']}",
                    reference=f"REFUND-{ref}",
                    meta={"bill_payment_id": record.id},
                )
                record.status = "failed"
                record.error_message = str(e)
                record.save()
                return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

            return Response({
                "status": "successful",
                "reference": ref,
                "token": record.token,
                "provider_reference": record.provider_reference,
                "message": "Electricity units vended successfully.",
            })

        else:
            # Async card/bank: return Flutterwave payment link
            try:
                payment_url = services.create_flutterwave_payment_link(
                    tx_ref=flw_tx_ref,
                    amount=amount,
                    currency="NGN",
                    customer_email=user.email,
                    customer_name=getattr(user, "get_full_name", lambda: user.email)(),
                    title="Electricity Bill Payment",
                    description=f"{data['provider']} — Meter {data['meter_number']}",
                    redirect_url=_get_redirect_url(),
                    meta=_build_flutterwave_meta_for_record("electricity", record.id),
                )
            except ValueError as e:
                record.status = "failed"
                record.error_message = str(e)
                record.save()
                return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

            return Response({
                "status": "pending",
                "reference": ref,
                "payment_url": payment_url,
                "message": "Complete payment via the link to process your electricity bill.",
            })


# ── Cable TV / Internet ───────────────────────────────────────────────────────

class CableInternetRenewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = CableRenewRequestSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        data = ser.validated_data
        user = request.user
        amount = Decimal(str(data["amount"]))
        payment_method = data["payment_method"]
        ref = services.generate_reference("CAB")
        flw_tx_ref = services.generate_reference("FLW-CAB")

        subscription = CableTVSubscription.objects.create(
            user=user,
            provider=data["provider"],
            provider_label=data["provider_label"],
            package_code=data["package_code"],
            package_label=data["package_label"],
            iuc_number=data["iuc_number"],
            account_name=data.get("account_name", ""),
            amount=amount,
            payment_method=payment_method,
            status="pending",
            transaction_reference=ref,
            flw_tx_ref=flw_tx_ref if payment_method != "wallet" else "",
        )

        if payment_method == "wallet":
            try:
                services.debit_wallet(
                    user=user,
                    amount=amount,
                    description=f"{data['provider_label']} — {data['package_label']}",
                    reference=ref,
                    meta={"cable_subscription_id": subscription.id},
                )
            except ValueError as e:
                subscription.status = "failed"
                subscription.error_message = str(e)
                subscription.save()
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            try:
                _execute_cable(subscription)
            except ValueError as e:
                services.refund_wallet(
                    user=user,
                    amount=amount,
                    description=f"Refund: {data['provider_label']} subscription failed",
                    reference=f"REFUND-{ref}",
                    meta={"cable_subscription_id": subscription.id},
                )
                subscription.status = "failed"
                subscription.error_message = str(e)
                subscription.save()
                return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

            return Response({
                "status": "successful",
                "reference": ref,
                "provider_reference": subscription.provider_reference,
                "message": f"{data['provider_label']} subscription activated.",
            })

        else:
            try:
                payment_url = services.create_flutterwave_payment_link(
                    tx_ref=flw_tx_ref,
                    amount=amount,
                    currency="NGN",
                    customer_email=user.email,
                    customer_name=getattr(user, "get_full_name", lambda: user.email)(),
                    title=f"{data['provider_label']} Subscription",
                    description=data["package_label"],
                    redirect_url=_get_redirect_url(),
                    meta=_build_flutterwave_meta_for_record("cable", subscription.id),
                )
            except ValueError as e:
                subscription.status = "failed"
                subscription.error_message = str(e)
                subscription.save()
                return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

            return Response({
                "status": "pending",
                "reference": ref,
                "payment_url": payment_url,
                "message": "Complete payment to activate your subscription.",
            })


# ── Education Fees ────────────────────────────────────────────────────────────

class EducationFeePayView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = EducationFeePayRequestSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        data = ser.validated_data
        user = request.user
        amount = Decimal(str(data["amount"]))
        payment_method = data["payment_method"]
        ref = services.generate_reference("EDU")
        flw_tx_ref = services.generate_reference("FLW-EDU")

        record = BillPaymentRecord.objects.create(
            user=user,
            bill_type="education",
            payment_method=payment_method,
            status="pending",
            amount=amount,
            transaction_reference=ref,
            flw_tx_ref=flw_tx_ref if payment_method != "wallet" else "",
            payload={
                "provider": data["provider"],
                "fee_type": data["fee_type"],
                "candidate_name": data.get("candidate_name", ""),
                "reg_no": data.get("reg_no", ""),
            },
        )

        if payment_method == "wallet":
            try:
                services.debit_wallet(
                    user=user,
                    amount=amount,
                    description=f"{data['provider_label']} — {data['fee_type_label']}",
                    reference=ref,
                    meta={"bill_payment_id": record.id},
                )
            except ValueError as e:
                record.status = "failed"
                record.error_message = str(e)
                record.save()
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            try:
                _execute_education(record)
            except ValueError as e:
                services.refund_wallet(
                    user=user,
                    amount=amount,
                    description=f"Refund: {data['provider_label']} payment failed",
                    reference=f"REFUND-{ref}",
                    meta={"bill_payment_id": record.id},
                )
                record.status = "failed"
                record.error_message = str(e)
                record.save()
                return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

            return Response({
                "status": "successful",
                "reference": ref,
                "token": record.token,
                "provider_reference": record.provider_reference,
                "message": f"{data['provider_label']} payment processed.",
            })

        else:
            try:
                payment_url = services.create_flutterwave_payment_link(
                    tx_ref=flw_tx_ref,
                    amount=amount,
                    currency="NGN",
                    customer_email=user.email,
                    customer_name=getattr(user, "get_full_name", lambda: user.email)(),
                    title=f"{data['provider_label']} Fee Payment",
                    description=data["fee_type_label"],
                    redirect_url=_get_redirect_url(),
                    meta=_build_flutterwave_meta_for_record("education", record.id),
                )
            except ValueError as e:
                record.status = "failed"
                record.error_message = str(e)
                record.save()
                return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

            return Response({
                "status": "pending",
                "reference": ref,
                "payment_url": payment_url,
                "message": "Complete payment to process your education fee.",
            })


# ── Flutterwave Webhook ───────────────────────────────────────────────────────

class FlutterwaveBillWebhookView(APIView):
    """
    Receives Flutterwave webhook for bill payments.
    Verifies signature, confirms payment, then executes PremiumSub bill.
    """
    permission_classes = []  # public — signature-verified

    def post(self, request):
        import hashlib
        import hmac

        secret_hash = getattr(settings, "FLUTTERWAVE_WEBHOOK_HASH", "")
        received_hash = request.headers.get("Verif-Hash", "")

        if secret_hash and received_hash != secret_hash:
            logger.warning("FLW bill webhook: invalid hash signature")
            return Response({"detail": "Invalid signature"}, status=status.HTTP_401_UNAUTHORIZED)

        payload = request.data
        event = payload.get("event", "")
        if event != "charge.completed":
            return Response({"detail": "ignored"}, status=status.HTTP_200_OK)

        flw_data = payload.get("data", {})
        if flw_data.get("status") != "successful":
            return Response({"detail": "payment not successful"}, status=status.HTTP_200_OK)

        tx_ref = flw_data.get("tx_ref", "")
        flw_transaction_id = str(flw_data.get("id", ""))
        meta = flw_data.get("meta", {}) or {}

        record_type = meta.get("record_type")
        record_id = meta.get("record_id")

        if not record_type or not record_id:
            logger.error("FLW bill webhook: missing meta record_type/record_id in tx_ref=%s", tx_ref)
            return Response({"detail": "meta missing"}, status=status.HTTP_200_OK)

        # Verify with Flutterwave
        try:
            from wallet.payment_gateway.flutterwave_service import verify_payment
            verified = verify_payment(flw_transaction_id)
            if not verified or verified.get("data", {}).get("status") != "successful":
                logger.error("FLW bill webhook: verification failed for tx %s", flw_transaction_id)
                return Response({"detail": "verification failed"}, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.exception("FLW bill webhook: verification error: %s", exc)
            return Response({"detail": "verification error"}, status=status.HTTP_200_OK)

        amount = Decimal(str(flw_data.get("amount", 0)))

        try:
            if record_type == "electricity":
                record = BillPaymentRecord.objects.get(id=record_id, bill_type="electricity")
                if record.status in ("successful", "failed"):
                    return Response({"detail": "already processed"}, status=status.HTTP_200_OK)
                record.flw_transaction_id = flw_transaction_id
                record.save(update_fields=["flw_transaction_id"])
                _execute_electricity(record)

            elif record_type == "cable":
                sub = CableTVSubscription.objects.get(id=record_id)
                if sub.status in ("successful", "failed"):
                    return Response({"detail": "already processed"}, status=status.HTTP_200_OK)
                sub.flw_transaction_id = flw_transaction_id
                sub.save(update_fields=["flw_transaction_id"])
                _execute_cable(sub)

            elif record_type == "education":
                record = BillPaymentRecord.objects.get(id=record_id, bill_type="education")
                if record.status in ("successful", "failed"):
                    return Response({"detail": "already processed"}, status=status.HTTP_200_OK)
                record.flw_transaction_id = flw_transaction_id
                record.save(update_fields=["flw_transaction_id"])
                _execute_education(record)

            else:
                logger.error("FLW bill webhook: unknown record_type=%s", record_type)

        except Exception as exc:
            logger.exception("FLW bill webhook: execution error for %s#%s: %s", record_type, record_id, exc)

        return Response({"detail": "ok"}, status=status.HTTP_200_OK)


# ── Payment status check ──────────────────────────────────────────────────────

class BillPaymentStatusView(APIView):
    """Check the status of any bill payment by reference."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ref = request.query_params.get("ref")
        if not ref:
            return Response({"detail": "ref query param required"}, status=status.HTTP_400_BAD_REQUEST)

        # Check all record types
        record = BillPaymentRecord.objects.filter(
            user=request.user, transaction_reference=ref
        ).first()
        if record:
            return Response({
                "status": record.status,
                "reference": record.transaction_reference,
                "token": record.token,
                "provider_reference": record.provider_reference,
                "bill_type": record.bill_type,
                "amount": str(record.amount),
                "created_at": record.created_at,
                "completed_at": record.completed_at,
            })

        sub = CableTVSubscription.objects.filter(
            user=request.user, transaction_reference=ref
        ).first()
        if sub:
            return Response({
                "status": sub.status,
                "reference": sub.transaction_reference,
                "provider_reference": sub.provider_reference,
                "bill_type": "cable",
                "provider": sub.provider_label,
                "package": sub.package_label,
                "amount": str(sub.amount),
                "created_at": sub.created_at,
                "completed_at": sub.completed_at,
            })

        return Response({"detail": "Payment record not found."}, status=status.HTTP_404_NOT_FOUND)
