"""
PremiumSub / Maskawa API service layer for utility, cable TV, and education payments.
Base URL: https://premiumsub.com.ng/api

Known endpoints (same vendor that handles airtime/data):
  Airtime  → POST /api/topup/
  Data     → POST /api/data/
  Electricity → POST /api/electricity/
  Cable TV    → POST /api/cabletv/
  Education   → POST /api/education/
  Verify meter → GET /api/verify/electricity/ (or POST)

Flutterwave is used for card/bank/mobile-money payments.
"""
import json
import uuid
import logging
import requests
from decimal import Decimal
from django.conf import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://premiumsub.com.ng/api"
TIMEOUT = 30  # seconds


def _headers():
    api_key = getattr(settings, "MASKAWA_API_KEY", "")
    return {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json",
    }


def _parse_response(response, action: str) -> dict:
    """
    Parse PremiumSub response and raise ValueError on failure.
    Returns the full parsed JSON on success.
    """
    try:
        data = response.json()
    except Exception:
        raise ValueError(
            f"{action}: provider returned non-JSON response "
            f"(HTTP {response.status_code}, body: {response.text[:200]})"
        )

    if response.status_code not in (200, 201):
        msg = (
            data.get("message") or data.get("error") or
            data.get("detail") or str(data)
        )
        raise ValueError(f"{action} failed (HTTP {response.status_code}): {msg}")

    # PremiumSub uses various success indicators
    status_str = str(data.get("status") or data.get("Status") or "").lower()
    success_val = data.get("success")

    if status_str not in ("success", "successful", "200") and success_val is not True:
        msg = (
            data.get("message") or data.get("error") or
            data.get("response") or str(data)
        )
        raise ValueError(f"{action} rejected by provider: {msg}")

    return data


# ── Provider slug → PremiumSub disco_name codes ─────────────────────────────
# PremiumSub uses hyphenated names matching VTPass convention
ELECTRICITY_DISCO_MAP = {
    "ikeja-electric":        "ikeja-electric",
    "eko-electric":          "eko-electric",
    "abuja-electric":        "abuja-electric",
    "kano-electric":         "kano-electric",
    "portharcourt-electric": "portharcourt-electric",
    "jos-electric":          "jos-electric",
    "ibadan-electric":       "ibadan-electric",
    "kaduna-electric":       "kaduna-electric",
    "benin-electric":        "benin-electric",
    "enugu-electric":        "enugu-electric",
}

CABLE_SERVICE_MAP = {
    "dstv":       "dstv",
    "gotv":       "gotv",
    "startimes":  "startimes",
    "showmax":    "showmax",
    "spectranet": "spectranet",
    "smile":      "smile",
}

EDUCATION_SERVICE_MAP = {
    "waec":       "waec",
    "neco":       "neco",
    "jamb":       "jamb",
    "nabteb":     "nabteb",
    "university": "university",
    "others":     "others",
}


# ── Meter verification ───────────────────────────────────────────────────────

def verify_meter(disco: str, meter_number: str, meter_type: str) -> dict:
    """
    Verify a meter number with the electricity provider before payment.
    Returns dict: {customer_name, address, meter_number, minimum_amount}
    Raises ValueError if verification fails.
    """
    disco_code = ELECTRICITY_DISCO_MAP.get(disco.lower(), disco.lower())

    # PremiumSub meter verification endpoint
    payload = json.dumps({
        "disco_name": disco_code,
        "meter_number": meter_number,
        "MeterType": meter_type,   # "prepaid" | "postpaid"
    })

    try:
        resp = requests.post(
            f"{BASE_URL}/verifymeter/",
            headers=_headers(),
            data=payload,
            timeout=TIMEOUT,
        )
    except requests.RequestException as exc:
        raise ValueError(f"Meter verification network error: {exc}")

    try:
        data = resp.json()
    except Exception:
        raise ValueError(f"Meter verification: invalid response (HTTP {resp.status_code})")

    if resp.status_code not in (200, 201):
        msg = data.get("message") or data.get("error") or str(data)
        raise ValueError(f"Meter verification failed: {msg}")

    # Check success at business level
    status_str = str(data.get("status") or data.get("Status") or "").lower()
    success_val = data.get("success")
    if status_str not in ("success", "successful", "200") and success_val is not True:
        msg = data.get("message") or data.get("error") or str(data)
        raise ValueError(f"Meter not found: {msg}")

    info = data.get("data") or data
    return {
        "customer_name": info.get("Customer_Name") or info.get("customer_name") or "",
        "address":       info.get("Address") or info.get("address") or "",
        "meter_number":  info.get("Meter_Number") or meter_number,
        "minimum_amount": int(info.get("Minimum_Amount") or info.get("minimum_amount") or 500),
        "raw": data,
    }


# ── Electricity vending ──────────────────────────────────────────────────────

def purchase_electricity(
    provider: str,
    meter_type: str,       # "prepaid" | "postpaid"
    meter_number: str,
    amount: Decimal,
    reference: str,
    phone: str = "",
) -> dict:
    """
    Vend electricity units via PremiumSub.
    Returns dict: {provider_reference, token, raw_response}
    Raises ValueError on failure.
    """
    disco_code = ELECTRICITY_DISCO_MAP.get(provider.lower(), provider.lower())

    payload = json.dumps({
        "disco_name":    disco_code,
        "amount":        int(amount),
        "meter_number":  meter_number,
        "MeterType":     meter_type,          # PremiumSub uses "MeterType" with capital M
        "mobile_number": phone or "",
        "request_id":    reference,
    })

    logger.info("Electricity purchase: disco=%s meter=%s amount=%s ref=%s", disco_code, meter_number, amount, reference)

    try:
        resp = requests.post(
            f"{BASE_URL}/electricity/",
            headers=_headers(),
            data=payload,
            timeout=TIMEOUT,
        )
    except requests.RequestException as exc:
        raise ValueError(f"Electricity API network error: {exc}")

    data = _parse_response(resp, "Electricity purchase")

    # Extract token and reference from response
    resp_data = data.get("data") or {}
    token = (
        resp_data.get("token") or
        resp_data.get("Token") or
        data.get("token") or ""
    )
    provider_ref = (
        resp_data.get("reference") or
        resp_data.get("requestId") or
        data.get("reference") or
        reference
    )

    logger.info("Electricity purchase OK: ref=%s token=%s provider_ref=%s", reference, bool(token), provider_ref)
    return {"provider_reference": provider_ref, "token": token, "raw_response": data}


# ── Cable TV / Internet ──────────────────────────────────────────────────────

def renew_cable_subscription(
    provider: str,
    iuc_number: str,
    package_code: str,
    amount: Decimal,
    reference: str,
    phone: str = "",
) -> dict:
    """
    Renew cable TV or internet subscription via PremiumSub.
    Returns dict: {provider_reference, raw_response}
    """
    service_code = CABLE_SERVICE_MAP.get(provider.lower(), provider.lower())

    payload = json.dumps({
        "cable_name":   service_code,
        "cable_plan":   package_code,     # variation_code / bouquet code
        "smartcard_no": iuc_number,
        "amount":       int(amount),
        "mobile_number": phone or "",
        "request_id":   reference,
    })

    logger.info("Cable renewal: provider=%s iuc=%s plan=%s ref=%s", service_code, iuc_number, package_code, reference)

    try:
        resp = requests.post(
            f"{BASE_URL}/cabletv/",
            headers=_headers(),
            data=payload,
            timeout=TIMEOUT,
        )
    except requests.RequestException as exc:
        raise ValueError(f"Cable TV API network error: {exc}")

    data = _parse_response(resp, "Cable TV subscription")

    resp_data = data.get("data") or {}
    provider_ref = (
        resp_data.get("reference") or
        data.get("reference") or reference
    )

    logger.info("Cable renewal OK: ref=%s provider_ref=%s", reference, provider_ref)
    return {"provider_reference": provider_ref, "raw_response": data}


# ── Education fees ───────────────────────────────────────────────────────────

def purchase_education_pin(
    provider: str,       # waec | neco | jamb | nabteb | university | others
    fee_type: str,       # variation/fee_type code
    amount: Decimal,
    reference: str,
    candidate_name: str = "",
    reg_no: str = "",
    phone: str = "",
) -> dict:
    """
    Purchase education result-checker PIN or registration.
    Returns dict: {provider_reference, token, raw_response}
    """
    service_code = EDUCATION_SERVICE_MAP.get(provider.lower(), provider.lower())

    payload = json.dumps({
        "exam_name":    service_code,
        "exam_type":    fee_type,
        "amount":       int(amount),
        "reg_number":   reg_no or "0000000000",
        "mobile_number": phone or "",
        "request_id":   reference,
        "student_name": candidate_name,
    })

    logger.info("Education fee: provider=%s fee_type=%s amount=%s ref=%s", service_code, fee_type, amount, reference)

    try:
        resp = requests.post(
            f"{BASE_URL}/education/",
            headers=_headers(),
            data=payload,
            timeout=TIMEOUT,
        )
    except requests.RequestException as exc:
        raise ValueError(f"Education API network error: {exc}")

    data = _parse_response(resp, "Education fee purchase")

    resp_data = data.get("data") or {}
    token = (
        resp_data.get("Pin") or resp_data.get("pin") or
        resp_data.get("token") or data.get("token") or ""
    )
    provider_ref = (
        resp_data.get("reference") or
        data.get("reference") or reference
    )

    logger.info("Education fee OK: ref=%s pin=%s", reference, bool(token))
    return {"provider_reference": provider_ref, "token": token, "raw_response": data}


# ── Wallet helpers ─────────────────────────────────────────────────────────────────────

def debit_wallet(user, amount, description, reference, meta=None):
    """Atomically debit wallet and record WalletTransaction. Raises ValueError if insufficient."""
    from decimal import Decimal
    from django.db import transaction as db_tx
    from wallet.models import Wallet
    from wallet.transactions.models import WalletTransaction

    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))

    with db_tx.atomic():
        try:
            wallet = Wallet.objects.select_for_update().get(user=user)
        except Wallet.DoesNotExist:
            raise ValueError("No wallet found for your account. Please contact support.")

        if not wallet.is_active:
            raise ValueError("Your wallet is currently inactive. Please contact support.")

        if wallet.balance < amount:
            shortfall = amount - wallet.balance
            raise ValueError(
                f"Insufficient wallet balance. "
                f"You need ₦{shortfall:,.2f} more. "
                f"Current balance: ₦{wallet.balance:,.2f}."
            )

        wallet.balance -= amount
        wallet.save(update_fields=["balance"])

        WalletTransaction.objects.create(
            user=user, wallet=wallet,
            transaction_type="payment", amount=amount,
            currency=wallet.currency or "NGN", status="successful",
            reference=reference, description=description, meta=meta or {},
        )
        logger.info("Wallet debited: user=%s amount=%s ref=%s", user, amount, reference)


def refund_wallet(user, amount, description, reference, meta=None):
    """Refund a previously debited amount back to wallet."""
    from decimal import Decimal
    from django.db import transaction as db_tx
    from wallet.models import Wallet
    from wallet.transactions.models import WalletTransaction

    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))

    with db_tx.atomic():
        try:
            wallet = Wallet.objects.select_for_update().get(user=user)
        except Wallet.DoesNotExist:
            logger.error("Refund failed — no wallet for user=%s ref=%s", user, reference)
            return

        wallet.balance += amount
        wallet.save(update_fields=["balance"])

        WalletTransaction.objects.create(
            user=user, wallet=wallet,
            transaction_type="refund", amount=amount,
            currency=wallet.currency or "NGN", status="successful",
            reference=reference, description=description, meta=meta or {},
        )
        logger.info("Wallet refunded: user=%s amount=%s ref=%s", user, amount, reference)


# ── Flutterwave checkout ───────────────────────────────────────────────────────────────────────

def create_flutterwave_payment_link(tx_ref, amount, currency, customer_email,
                                     customer_name, title, description,
                                     redirect_url, meta=None):
    """Create a Flutterwave standard checkout payment link. Returns URL string."""
    import requests as rq
    from decimal import Decimal
    secret_key = getattr(settings, "FLUTTERWAVE_SECRET_KEY", "")
    if not secret_key:
        raise ValueError("Payment gateway not configured. Please contact support.")

    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))

    payload = {
        "tx_ref": tx_ref,
        "amount": float(amount),
        "currency": currency,
        "redirect_url": redirect_url,
        "payment_options": "card,banktransfer,ussd,mobilemoney",
        "customer": {"email": customer_email, "name": customer_name or customer_email},
        "customizations": {
            "title": title,
            "description": description,
            "logo": getattr(settings, "BRAND_LOGO_URL", ""),
        },
        "meta": meta or {},
    }

    try:
        resp = rq.post(
            "https://api.flutterwave.com/v3/payments",
            headers={"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"},
            json=payload, timeout=20,
        )
    except rq.RequestException as exc:
        raise ValueError(f"Payment gateway network error: {exc}")

    if resp.status_code not in (200, 201):
        raise ValueError(f"Payment gateway error (HTTP {resp.status_code}): {resp.text[:300]}")

    data = resp.json()
    link = (data.get("data") or {}).get("link")
    if not link:
        raise ValueError("Payment gateway did not return a checkout link.")

    logger.info("Flutterwave link created: tx_ref=%s amount=%s currency=%s", tx_ref, amount, currency)
    return link


# ── Utility ────────────────────────────────────────────────────────────────────────────

def generate_reference(prefix="GC"):
    import uuid
    return f"{prefix}-{uuid.uuid4().hex[:16].upper()}"
