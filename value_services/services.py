"""
PremiumSub / Maskawa API service layer for utility, cable TV, and education payments.
Docs: https://premiumsub.com.ng  (same vendor as airtime/data already integrated)

Electricity API uses BuyPower or IBEDC network under the hood.
Cable TV covers DSTV, GOtv, Startimes, ShowMax (OTT), Spectranet, Smile.
Education covers WAEC, NECO, JAMB, NABTEB result checker / registration.
"""
import json
import uuid
import requests
from decimal import Decimal
from django.conf import settings


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
        raise ValueError(f"{action}: provider returned non-JSON response (HTTP {response.status_code})")

    if response.status_code not in (200, 201):
        msg = (
            data.get("message") or data.get("error") or
            data.get("detail") or str(data)
        )
        raise ValueError(f"{action} failed (HTTP {response.status_code}): {msg}")

    # Check business-level success
    status_str = str(
        data.get("status") or data.get("Status") or ""
    ).lower()
    success_val = data.get("success")

    if status_str not in ("success", "successful", "200") and success_val is not True:
        msg = (
            data.get("message") or data.get("error") or
            data.get("response") or str(data)
        )
        raise ValueError(f"{action} rejected by provider: {msg}")

    return data


# ── Provider slug → PremiumSub service IDs ──────────────────────────────────

ELECTRICITY_SERVICE_IDS = {
    "ikeja-electric":   "ikeja-electric",
    "eko-electric":     "eko-electric",
    "abuja-electric":   "abuja-electric",
    "kano-electric":    "kano-electric",
    "portharcourt-electric": "portharcourt-electric",
    "jos-electric":     "jos-electric",
    "ibadan-electric":  "ibadan-electric",
    "kaduna-electric":  "kaduna-electric",
}

CABLE_SERVICE_IDS = {
    "dstv":       "dstv",
    "gotv":       "gotv",
    "startimes":  "startimes",
    "showmax":    "showmax",
    "spectranet": "spectranet",
    "smile":      "smile",
}

EDUCATION_SERVICE_IDS = {
    "waec":   "waec",
    "neco":   "neco",
    "jamb":   "jamb",
    "nabteb": "nabteb",
}


# ── Electricity ──────────────────────────────────────────────────────────────

def purchase_electricity(
    provider: str,
    meter_type: str,       # "prepaid" | "postpaid"
    meter_number: str,
    amount: Decimal,
    reference: str,
) -> dict:
    """
    Vend electricity units.
    Returns dict with keys: provider_reference, token (for prepaid), raw_response
    """
    service_id = ELECTRICITY_SERVICE_IDS.get(provider.lower(), provider.lower())
    payload = json.dumps({
        "serviceID": service_id,
        "billersCode": meter_number,
        "variation_code": meter_type,   # prepaid | postpaid
        "amount": int(amount),
        "phone": "",                    # optional — customer phone for receipt SMS
        "request_id": reference,
    })
    resp = requests.post(f"{BASE_URL}/electricity/", headers=_headers(), data=payload, timeout=TIMEOUT)
    data = _parse_response(resp, "Electricity purchase")

    token = (
        (data.get("data") or {}).get("token") or
        data.get("token") or ""
    )
    provider_ref = (
        (data.get("data") or {}).get("reference") or
        data.get("reference") or
        (data.get("data") or {}).get("requestId") or
        reference
    )
    return {"provider_reference": provider_ref, "token": token, "raw_response": data}


# ── Cable TV ─────────────────────────────────────────────────────────────────

def renew_cable_subscription(
    provider: str,
    iuc_number: str,
    package_code: str,
    amount: Decimal,
    reference: str,
) -> dict:
    """
    Renew cable TV / internet subscription.
    Returns dict with: provider_reference, raw_response
    """
    service_id = CABLE_SERVICE_IDS.get(provider.lower(), provider.lower())
    payload = json.dumps({
        "serviceID": service_id,
        "billersCode": iuc_number,
        "variation_code": package_code,
        "amount": int(amount),
        "phone": "",
        "request_id": reference,
    })
    resp = requests.post(f"{BASE_URL}/cabletv/", headers=_headers(), data=payload, timeout=TIMEOUT)
    data = _parse_response(resp, "Cable TV subscription")

    provider_ref = (
        (data.get("data") or {}).get("reference") or
        data.get("reference") or reference
    )
    return {"provider_reference": provider_ref, "raw_response": data}


# ── Education ────────────────────────────────────────────────────────────────

def purchase_education_pin(
    provider: str,       # waec | neco | jamb | nabteb
    fee_type: str,       # variation_code e.g. "waec-registration"
    amount: Decimal,
    reference: str,
    candidate_name: str = "",
    reg_no: str = "",
) -> dict:
    """
    Purchase education result checker PIN or registration.
    Returns dict with: provider_reference, token (PIN), raw_response
    """
    service_id = EDUCATION_SERVICE_IDS.get(provider.lower(), provider.lower())
    payload = json.dumps({
        "serviceID": service_id,
        "variation_code": fee_type,
        "amount": int(amount),
        "billersCode": reg_no or "0000000000",
        "phone": "",
        "request_id": reference,
        "Beneficiary_name": candidate_name,
    })
    resp = requests.post(f"{BASE_URL}/education/", headers=_headers(), data=payload, timeout=TIMEOUT)
    data = _parse_response(resp, "Education fee purchase")

    token = (
        (data.get("data") or {}).get("Pin") or
        (data.get("data") or {}).get("token") or
        data.get("token") or ""
    )
    provider_ref = (
        (data.get("data") or {}).get("reference") or
        data.get("reference") or reference
    )
    return {"provider_reference": provider_ref, "token": token, "raw_response": data}


# ── Wallet helpers (shared with views) ──────────────────────────────────────

def debit_wallet(user, amount: Decimal, description: str, reference: str, meta: dict = None) -> None:
    """
    Atomically debit a user's wallet and record a WalletTransaction.
    Raises ValueError if balance insufficient.
    """
    from django.db import transaction as db_tx
    from wallet.models import Wallet
    from wallet.transactions.models import WalletTransaction

    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))

    with db_tx.atomic():
        wallet = Wallet.objects.select_for_update().get(user=user)
        if wallet.balance < amount:
            raise ValueError("Insufficient wallet balance.")
        wallet.balance -= amount
        wallet.save(update_fields=["balance"])
        WalletTransaction.objects.create(
            user=user,
            wallet=wallet,
            transaction_type="payment",
            amount=amount,
            currency=wallet.currency or "NGN",
            status="successful",
            reference=reference,
            description=description,
            meta=meta or {},
        )


def refund_wallet(user, amount: Decimal, description: str, reference: str, meta: dict = None) -> None:
    """Refund a previously debited amount back to wallet."""
    from django.db import transaction as db_tx
    from wallet.models import Wallet
    from wallet.transactions.models import WalletTransaction

    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))

    with db_tx.atomic():
        wallet = Wallet.objects.select_for_update().get(user=user)
        wallet.balance += amount
        wallet.save(update_fields=["balance"])
        WalletTransaction.objects.create(
            user=user,
            wallet=wallet,
            transaction_type="refund",
            amount=amount,
            currency=wallet.currency or "NGN",
            status="successful",
            reference=reference,
            description=description,
            meta=meta or {},
        )


# ── Flutterwave payment link helper ─────────────────────────────────────────

def create_flutterwave_payment_link(
    tx_ref: str,
    amount: Decimal,
    currency: str,
    customer_email: str,
    customer_name: str,
    title: str,
    description: str,
    redirect_url: str,
    meta: dict = None,
) -> str:
    """
    Create a Flutterwave standard checkout URL.
    Returns the payment URL to redirect the user to.
    """
    secret_key = getattr(settings, "FLUTTERWAVE_SECRET_KEY", "")
    payload = {
        "tx_ref": tx_ref,
        "amount": float(amount),
        "currency": currency,
        "redirect_url": redirect_url,
        "payment_options": "card,banktransfer,ussd,mobilemoney",
        "customer": {
            "email": customer_email,
            "name": customer_name,
        },
        "customizations": {
            "title": title,
            "description": description,
            "logo": "",
        },
        "meta": meta or {},
    }
    resp = requests.post(
        "https://api.flutterwave.com/v3/payments",
        headers={
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=20,
    )
    if resp.status_code not in (200, 201):
        raise ValueError(f"Flutterwave checkout init failed: {resp.text[:300]}")
    data = resp.json()
    link = data.get("data", {}).get("link")
    if not link:
        raise ValueError("Flutterwave did not return a payment link.")
    return link


def generate_reference(prefix: str = "GC") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:16].upper()}"
