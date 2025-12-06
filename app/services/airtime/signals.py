from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.conf import settings
from decimal import Decimal
from django.core.exceptions import ValidationError

from .models import AirtimePurchase, DataPurchase, NetworkProvider
from wallet.models import Wallet
from wallet.transactions.models import WalletTransaction

import requests
import json

# --- COMMON PROVIDER API LOGIC (Airtime & Data) ---

def get_wallet_and_validate_balance(user, amount, purchase_type="purchase"):
    try:
        wallet = Wallet.objects.get(user=user)
    except Wallet.DoesNotExist:
        raise ValidationError("Wallet does not exist for the user.")

    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    if wallet.balance < amount:
        raise ValidationError(
            f"Insufficient wallet balance to complete this {purchase_type}."
        )
    return wallet, amount

def call_maskawa_api_for_airtime(instance, api_key):
    provider = instance.provider
    network_code = getattr(provider, "value", None)
    if not network_code:
        raise ValidationError("Cannot determine provider code for API")

    provider_code_to_id = {
        "mtn": 1,
        "glo": 2,
        "9mobile": 3,
        "airtel": 4,
    }
    network_id = provider_code_to_id.get(str(network_code).strip().lower())
    if not network_id:
        raise ValidationError(f"Unknown provider code '{network_code}' for Maskawa API")

    payload_dict = {
        "network": str(network_id),
        "amount": int(instance.amount),
        "mobile_number": instance.phone,
        "Ported_number": False,
        "airtime_type": "VTU",
    }
    payload = json.dumps(payload_dict)
    url = "https://premiumsub.com.ng/api/topup/"
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, headers=headers, data=payload, timeout=20)
    except Exception as e:
        raise ValidationError(f"Airtime purchase API request could not be completed: {str(e)}")
    return response

def call_maskawa_api_for_data(instance, api_key):
    provider = instance.provider
    network_code = getattr(provider, "value", None)
    if not network_code:
        raise ValidationError("Cannot determine provider code for API")

    provider_code_to_id = {
        "mtn": 1,
        "glo": 2,
        "9mobile": 3,
        "airtel": 4,
    }
    network_id = provider_code_to_id.get(str(network_code).strip().lower())
    if not network_id:
        raise ValidationError(f"Unknown provider code '{network_code}' for Maskawa API")

    # To get plan identifier
    plan_code = getattr(instance.plan, "value", None)
    if not plan_code:
        raise ValidationError("Cannot determine plan code for API")

    payload_dict = {
        "network": str(network_id),
        "plan": str(plan_code),
        "mobile_number": instance.phone,
        "Ported_number": False,
        "datatype": "data",
    }
    payload = json.dumps(payload_dict)
    url = "https://premiumsub.com.ng/api/datashare/"
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, headers=headers, data=payload, timeout=20)
    except Exception as e:
        raise ValidationError(f"Data purchase API request could not be completed: {str(e)}")
    return response

def handle_provider_response(instance, response, purchase_type="purchase"):
    status_code = getattr(response, "status_code", None)
    if status_code is None or status_code not in (200, 201):
        api_error_detail = getattr(response, "text", "")
        raise ValidationError(
            f"{purchase_type.capitalize()} API request failed or was not reachable. (HTTP status: {status_code}) Details: {api_error_detail}"
        )
    try:
        maskawa_resp = response.json()
    except Exception as e:
        raw = getattr(response, "text", "")
        raise ValidationError("Provider response was not valid JSON")

    api_success = (
        (str(maskawa_resp.get("status", "")).lower() == "success")
        or (str(maskawa_resp.get("Status", "")).lower() == "success")
        or (str(maskawa_resp.get("status", "")).lower() == "successful")
        or (str(maskawa_resp.get("Status", "")).lower() == "successful")
        or (maskawa_resp.get("success") is True)
    )
    if not api_success:
        api_error_message = (
            maskawa_resp.get("message")
            or maskawa_resp.get("error")
            or maskawa_resp.get("response")
            or maskawa_resp
        )
        raise ValidationError(f"Provider: {purchase_type.capitalize()} failed: {api_error_message}")

    # Accept both "reference"/"ident" etc.
    provider_ref = (
        (maskawa_resp.get("data") or {}).get("reference")
        or maskawa_resp.get("reference")
        or maskawa_resp.get("provider_ref")
        or (maskawa_resp.get("data") or {}).get("ident")
        or maskawa_resp.get("ident")
    )
    if not provider_ref:
        raise ValidationError(f"Provider did not return a valid reference for this {purchase_type}.")

    instance.external_ref = provider_ref
    instance.status_message = str(maskawa_resp)
    instance.completed = True

# --- AIRTIME LOGIC ---

@receiver(pre_save, sender=AirtimePurchase)
def process_airtime_and_validate_wallet(sender, instance, **kwargs):
    user = instance.user
    wallet, amount = get_wallet_and_validate_balance(user, instance.amount, "airtime purchase")
    if not instance.external_ref:
        api_key = getattr(settings, "MASKAWA_API_KEY", None)
        if not api_key:
            raise ValidationError("No API key configured for Maskawa provider.")
        response = call_maskawa_api_for_airtime(instance, api_key)
        handle_provider_response(instance, response, "airtime purchase")

@receiver(post_save, sender=AirtimePurchase)
def create_wallet_transaction_for_airtime(sender, instance, created, **kwargs):
    if instance.completed:
        reference = f"airtime-{instance.pk}"
        existing = WalletTransaction.objects.filter(reference=reference).first()
        if existing:
            return
        try:
            wallet = Wallet.objects.get(user=instance.user)
        except Wallet.DoesNotExist:
            return

        amount = getattr(instance, "amount")
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        if wallet.balance < amount:
            return

        provider_label = getattr(instance.provider, "label", None)
        if provider_label:
            description = f"Airtime purchase of {amount} NGN for {instance.phone} on {provider_label}"
        else:
            description = f"Airtime purchase of {amount} NGN"

        WalletTransaction.objects.create(
            user=instance.user,
            wallet=wallet,
            transaction_type='payment',
            amount=amount,
            currency='NGN',
            status='successful',
            reference=reference,
            description=description,
            meta={
                "airtime_purchase_id": instance.pk,
                "phone": instance.phone,
                "external_ref": instance.external_ref,
                "status_message": instance.status_message,
            }
        )

# --- DATA PURCHASE LOGIC ---

@receiver(pre_save, sender=DataPurchase)
def process_dataplan_and_validate_wallet(sender, instance, **kwargs):
    user = instance.user
    wallet, amount = get_wallet_and_validate_balance(user, instance.amount, "data plan purchase")
    if not instance.external_ref:
        api_key = getattr(settings, "MASKAWA_API_KEY", None)
        if not api_key:
            raise ValidationError("No API key configured for Maskawa provider.")
        response = call_maskawa_api_for_data(instance, api_key)
        handle_provider_response(instance, response, "data plan purchase")

@receiver(post_save, sender=DataPurchase)
def create_wallet_transaction_for_dataplan(sender, instance, created, **kwargs):
    if instance.completed:
        reference = f"data-{instance.pk}"
        existing = WalletTransaction.objects.filter(reference=reference).first()
        if existing:
            return
        try:
            wallet = Wallet.objects.get(user=instance.user)
        except Wallet.DoesNotExist:
            return

        amount = getattr(instance, "amount")
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        if wallet.balance < amount:
            return

        provider_label = getattr(instance.provider, "label", None)
        plan_label = getattr(instance.plan, "label", None)
        if provider_label and plan_label:
            description = f"Data plan '{plan_label}' ({amount} NGN) for {instance.phone} on {provider_label}"
        else:
            description = f"Data plan purchase ({amount} NGN)"

        WalletTransaction.objects.create(
            user=instance.user,
            wallet=wallet,
            transaction_type='payment',
            amount=amount,
            currency='NGN',
            status='successful',
            reference=reference,
            description=description,
            meta={
                "data_purchase_id": instance.pk,
                "phone": instance.phone,
                "external_ref": instance.external_ref,
                "status_message": instance.status_message,
            }
        )
