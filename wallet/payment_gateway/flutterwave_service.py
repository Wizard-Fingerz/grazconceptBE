"""
Flutterwave payment gateway service.

Handles:
  - Generating transaction references
  - Verifying payments after inline checkout
  - Initiating bank transfers (withdrawals)
  - Verifying transfer status
  - Validating webhook signatures
"""
import hashlib
import hmac
import uuid
from decimal import Decimal

import requests
from django.conf import settings


FLW_BASE_URL = "https://api.flutterwave.com/v3"
SECRET_KEY = getattr(settings, "FLUTTERWAVE_SECRET_KEY", "")
WEBHOOK_HASH = getattr(settings, "FLUTTERWAVE_WEBHOOK_HASH", "")


def _headers():
    return {
        "Authorization": f"Bearer {SECRET_KEY}",
        "Content-Type": "application/json",
    }


def generate_reference(prefix: str = "GC") -> str:
    """Create a unique transaction reference."""
    return f"{prefix}-{uuid.uuid4().hex[:16].upper()}"


def verify_payment(flw_transaction_id: int) -> dict:
    """
    Verify a completed inline payment with Flutterwave.
    Returns the Flutterwave response dict (data key).
    Raises ValueError on failure.
    """
    url = f"{FLW_BASE_URL}/transactions/{flw_transaction_id}/verify"
    resp = requests.get(url, headers=_headers(), timeout=30)
    data = resp.json()
    if data.get("status") != "success":
        raise ValueError(data.get("message", "Flutterwave verification failed"))
    return data["data"]


def initiate_transfer(
    *,
    account_bank: str,
    account_number: str,
    amount: Decimal,
    narration: str,
    currency: str = "NGN",
    reference: str = None,
    beneficiary_name: str = "",
) -> dict:
    """
    Initiate a bank transfer (withdrawal payout) via Flutterwave.
    Returns Flutterwave response dict.
    """
    if reference is None:
        reference = generate_reference("GCW")
    payload = {
        "account_bank": account_bank,
        "account_number": account_number,
        "amount": float(amount),
        "narration": narration,
        "currency": currency,
        "reference": reference,
        "beneficiary_name": beneficiary_name,
        "debit_currency": currency,
    }
    url = f"{FLW_BASE_URL}/transfers"
    resp = requests.post(url, json=payload, headers=_headers(), timeout=30)
    data = resp.json()
    if data.get("status") not in ("success", "pending"):
        raise ValueError(data.get("message", "Flutterwave transfer failed"))
    return data


def verify_transfer(flw_transfer_id: int) -> dict:
    """Verify the status of a transfer (withdrawal)."""
    url = f"{FLW_BASE_URL}/transfers/{flw_transfer_id}"
    resp = requests.get(url, headers=_headers(), timeout=30)
    data = resp.json()
    if data.get("status") != "success":
        raise ValueError(data.get("message", "Transfer verification failed"))
    return data["data"]


def validate_webhook_signature(payload_bytes: bytes, received_hash: str) -> bool:
    """
    Validate that a webhook came from Flutterwave.
    Flutterwave sends: verif-hash header = your FLUTTERWAVE_WEBHOOK_HASH (plain string)
    """
    if not WEBHOOK_HASH:
        return False
    return received_hash == WEBHOOK_HASH


def get_banks(country: str = "NG") -> list:
    """Fetch list of Nigerian banks for withdrawal form."""
    url = f"{FLW_BASE_URL}/banks/{country}"
    resp = requests.get(url, headers=_headers(), timeout=30)
    data = resp.json()
    if data.get("status") == "success":
        return data.get("data", [])
    return []
