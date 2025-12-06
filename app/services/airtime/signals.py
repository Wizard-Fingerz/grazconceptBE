from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.conf import settings
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import AirtimePurchase, NetworkProvider
from wallet.models import Wallet
from wallet.transactions.models import WalletTransaction

import requests
import json

@receiver(pre_save, sender=AirtimePurchase)
def process_airtime_and_validate_wallet(sender, instance, **kwargs):
    """
    Before saving an AirtimePurchase, ensure API purchase is successful.
    If API airtime purchase fails, the AirtimePurchase object must NOT be created.
    """

    print("[Airtime SIGNALS][pre_save] Begin processing AirtimePurchase pre_save")
    user = instance.user
    try:
        print("[Airtime SIGNALS][pre_save] Fetching wallet for user:", user)
        wallet = Wallet.objects.get(user=user)
        print("[Airtime SIGNALS][pre_save] Wallet found:", wallet)
    except Wallet.DoesNotExist:
        print("[Airtime SIGNALS][pre_save] Wallet does not exist for user:", user)
        raise ValidationError("Wallet does not exist for the user.")

    amount = getattr(instance, "amount")
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
        print("[Airtime SIGNALS][pre_save] Converted amount to Decimal:", amount)

    print("[Airtime SIGNALS][pre_save] Checking wallet balance:", wallet.balance, "vs", amount)
    if wallet.balance < amount:
        print("[Airtime SIGNALS][pre_save] Insufficient wallet balance")
        raise ValidationError("Insufficient wallet balance to complete this airtime purchase.")

    print("[Airtime SIGNALS][pre_save] instance.completed:", instance.completed, "instance.external_ref:", instance.external_ref)
    # Only call the provider API if instance.external_ref is not set (i.e., new purchase)
    if not instance.external_ref:
        print("[Airtime SIGNALS][pre_save] About to call provider API because no external_ref exists.")
        provider = instance.provider
        network_code = getattr(provider, "value", None)
        print("[Airtime SIGNALS][pre_save] Provider:", provider, "network_code:", network_code)
        if not network_code:
            print("[Airtime SIGNALS][pre_save] No network_code for provider")
            raise ValidationError("Cannot determine provider code for API")

        api_key = getattr(settings, "MASKAWA_API_KEY", None)
        print("[Airtime SIGNALS][pre_save] MASKAWA_API_KEY:", "FOUND" if api_key else None)
        if not api_key:
            print("[Airtime SIGNALS][pre_save] No MASKAWA_API_KEY configured")
            raise ValidationError("No API key configured for Maskawa provider.")

        provider_code_to_id = {
            "mtn": 1,
            "glo": 2,
            "9mobile": 3,
            "airtel": 4,
        }
        network_id = provider_code_to_id.get(str(network_code).strip().lower())
        print("[Airtime SIGNALS][pre_save] network_id:", network_id)
        if not network_id:
            print("[Airtime SIGNALS][pre_save] Unknown provider code:", network_code)
            raise ValidationError(f"Unknown provider code '{network_code}' for Maskawa API")

        payload_dict = {
            "network": str(network_id),
            "amount": int(amount),
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
        print("[Airtime SIGNALS][pre_save] Payload ready:", payload)
        print("[Airtime SIGNALS][pre_save] URL:", url)
        print("[Airtime SIGNALS][pre_save] Headers:", headers)

        try:
            print("[Airtime SIGNALS][pre_save] Making POST request to provider API.")
            response = requests.post(url, headers=headers, data=payload, timeout=20)
            print("[Airtime SIGNALS][pre_save] Provider API POST finished. Status code:", getattr(response, 'status_code', None))
        except Exception as e:
            print(f"[Airtime SIGNALS][pre_save] Exception during API POST: {e}")
            raise ValidationError(f"Airtime purchase API request could not be completed: {str(e)}")

        # Check for a valid status_code
        status_code = getattr(response, "status_code", None)
        if status_code is None or status_code not in (200, 201):
            api_error_detail = getattr(response, "text", "")
            print("[Airtime SIGNALS][pre_save] API error response body:", api_error_detail)
            raise ValidationError(
                f"Airtime API request failed or was not reachable. (HTTP status: {status_code}) Details: {api_error_detail}"
            )

        # Try to parse the response safely
        try:
            print("[Airtime SIGNALS][pre_save] Decoding provider JSON response.")
            maskawa_resp = response.json()
        except Exception as e:
            raw = getattr(response, "text", "")
            print(f"[Airtime SIGNALS][pre_save] Provider response was not valid JSON: {e}. Raw body: {raw}")
            raise ValidationError("Provider response was not valid JSON")

        print("[Airtime SIGNALS][pre_save] Provider JSON response:", maskawa_resp)

        # The API sometimes returns Status: 'successful' (as seen in logs); 
        # Sometimes it returns "status": "success", or "success": True; 
        # A failed transaction might even have Status: 'successful' but is not truly succeeded.
        # So, check a few keys to decide real API success.
        # Priority of checks: (1) "status" or "Status" == "success" or "successful", (2) "success" == True
        api_success = (
            (str(maskawa_resp.get("status", "")).lower() == "success")
            or (str(maskawa_resp.get("Status", "")).lower() == "success")
            or (str(maskawa_resp.get("status", "")).lower() == "successful")
            or (str(maskawa_resp.get("Status", "")).lower() == "successful")
            or (maskawa_resp.get("success") is True)
        )
        print("[Airtime SIGNALS][pre_save] API success status:", api_success)
        
        # If the API did not succeed, raise the error (showing the real API response/message)
        if not api_success:
            api_error_message = (
                maskawa_resp.get("message")
                or maskawa_resp.get("error")
                or maskawa_resp.get("response")
                or maskawa_resp
            )
            print("[Airtime SIGNALS][pre_save] Provider says failed:", api_error_message)
            raise ValidationError(f"Provider: Airtime purchase failed: {api_error_message}")

        # Look for provider reference (must be required); allow for common field names and structures
        provider_ref = (
            (maskawa_resp.get("data") or {}).get("reference")
            or maskawa_resp.get("reference")
            or maskawa_resp.get("provider_ref")
            or (maskawa_resp.get("data") or {}).get("ident")
            or maskawa_resp.get("ident")
        )
        print("[Airtime SIGNALS][pre_save] Provider reference:", provider_ref)
        if not provider_ref:
            print("[Airtime SIGNALS][pre_save] No valid provider_ref in API response. Full API response:", maskawa_resp)
            raise ValidationError("Provider did not return a valid reference for this airtime purchase.")

        print("[Airtime SIGNALS][pre_save] Airtime purchase succeeded. Setting instance fields.")
        instance.external_ref = provider_ref
        instance.status_message = str(maskawa_resp)
        instance.completed = True  # Mark as completed after successful external call
        print("[Airtime SIGNALS][pre_save] Instance processing complete.")


@receiver(post_save, sender=AirtimePurchase)
def create_wallet_transaction_for_airtime(sender, instance, created, **kwargs):
    """
    After successful AirtimePurchase (completed=True), create a debit WalletTransaction
    if one does not already exist. The wallet is only debited after provider confirms airtime.
    """
    print("[Airtime SIGNALS][post_save] Begin processing AirtimePurchase post_save")
    if instance.completed:
        reference = f"airtime-{instance.pk}"
        print(f"[Airtime SIGNALS][post_save] Checking for existing wallet tx with reference {reference}")
        existing = WalletTransaction.objects.filter(reference=reference).first()
        if existing:
            print(f"[Airtime SIGNALS][post_save] WalletTransaction already exists with reference {reference}")
            return

        try:
            print(f"[Airtime SIGNALS][post_save] Fetching wallet for user {instance.user}")
            wallet = Wallet.objects.get(user=instance.user)
            print(f"[Airtime SIGNALS][post_save] Wallet found: {wallet}")
        except Wallet.DoesNotExist:
            print("[Airtime SIGNALS][post_save] Wallet does not exist for user")
            return

        amount = getattr(instance, "amount")
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
            print("[Airtime SIGNALS][post_save] Converted amount to Decimal:", amount)

        print("[Airtime SIGNALS][post_save] Checking wallet balance before creating WalletTransaction:", wallet.balance, "vs", amount)
        if wallet.balance < amount:
            print("[Airtime SIGNALS][post_save] Insufficient funds at post_save, transaction not created.")
            return

        # Get provider label safely
        provider_label = getattr(instance.provider, "label", None)
        if provider_label:
            description = f"Airtime purchase of {amount} NGN for {instance.phone} on {provider_label}"
        else:
            description = f"Airtime purchase of {amount} NGN"

        print("[Airtime SIGNALS][post_save] Creating WalletTransaction with description:", description)

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
        print("[Airtime SIGNALS][post_save] WalletTransaction successfully created for purchase", instance.pk)
