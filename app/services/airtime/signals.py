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


# --- DATA PLAN MAPPING FOR PROVIDER API ---

# Maps DataPlan.value (or pk) to API plan id, dynamically loaded from DB on demand.
def get_api_plan_id_from_data_purchase(data_purchase):
    """
    Get the external API plan id to use for a DataPurchase instance (for /api/buydata).
    Assumes DataPlan.value matches a unique field or the plan pk should be used.
    Returns an integer plan id for the remote vendor API.
    """
    plan_map = {
        # 9MOBILE GIFTING
        "9mobile_500mb_gifting": 182,
        "9mobile_1.5gb_gifting": 183,
        "9mobile_2gb_gifting": 184,
        "9mobile_3gb_gifting": 185,
        "9mobile_4.5gb_gifting": 186,
        "9mobile_11gb_gifting": 187,
        "9mobile_15gb_gifting": 188,
        "9mobile_40gb_gifting": 189,
        "9mobile_75gb_gifting": 190,
        # AIRTEL GIFTING, AWOOF, CORPORATE
        "airtel_3.2gb_gifting_2days": 145,
        "airtel_2gb_gifting_2days": 146,
        "airtel_5gb_gifting_7days": 147,
        "airtel_10gb_gifting_7days": 148,
        "airtel_1gb_gifting_social_3days": 149,
        "airtel_8gb_gifting_monthlybinge": 150,
        "airtel_1.5gb_gifting_2days": 163,
        "airtel_500mb_gifting_7days": 164,
        "airtel_1gb_gifting_1day": 165,
        "airtel_1.5gb_gifting_social_7days": 191,
        "airtel_4gb_gifting_monthlybinge": 192,
        "airtel_1gb_gifting_7days": 193,
        "airtel_1gb_awoof_3days": 218,
        "airtel_2gb_awoof_1day": 219,
        "airtel_1.5gb_awoof_7days": 220,
        "airtel_2gb_awoof_2days": 221,
        "airtel_3gb_awoof_2days": 222,
        "airtel_3.5gb_gifting_7days": 254,
        "airtel_100mb_corporate_daily": 255,
        "airtel_300mb_corporate_daily": 256,
        "airtel_300mb_corporate_daily_alt": 257,
        "airtel_1gb_corporate_30days": 258,
        "airtel_500mb_corporate_7days": 259,
        "airtel_1.5gb_corporate_7days": 260,
        "airtel_3.5gb_corporate_7days": 261,
        "airtel_2gb_corporate_30days": 262,
        "airtel_3gb_corporate_30days": 264,
        "airtel_6gb_corporate_7days": 265,
        "airtel_4gb_corporate_30days": 266,
        "airtel_10gb_corporate_7days": 267,
        "airtel_8gb_corporate_30days": 268,
        "airtel_10gb_corporate_30days": 269,
        "airtel_18gb_corporate_7days": 270,
        "airtel_13gb_corporate_30days": 271,
        "airtel_25gb_corporate_30days": 272,
        "airtel_3.2gb_awoof_2days": 273,
        "airtel_1.5gb_awoof_1day": 274,
        "airtel_10gb_awoof_30days": 275,
        "airtel_600mb_awoof_2days": 276,
        "airtel_150mb_awoof_1day": 277,
        "airtel_300mb_awoof_2days": 278,
        "airtel_6.5gb_awoof_7days": 279,
        "airtel_5gb_awoof_7days": 280,
        "airtel_7gb_awoof_7days": 281,
        "airtel_6gb_awoof_7days": 282,
        "airtel_13gb_awoof_30days": 283,
        "airtel_18gb_awoof_7days": 284,
        # GLO CORPORATE GIFTING
        "glo_1gb_corporate_30days": 194,
        "glo_2gb_corporate_30days": 195,
        "glo_3gb_corporate_30days": 196,
        "glo_5gb_corporate_30days": 197,
        "glo_10gb_corporate_30days": 198,
        "glo_500mb_corporate_30days": 199,
        "glo_200mb_corporate_30days": 206,
        "glo_1gb_corporate_3days": 223,
        "glo_3gb_corporate_3days": 224,
        "glo_5gb_corporate_3days": 225,
        "glo_1gb_corporate_7days": 226,
        "glo_3gb_corporate_7days": 227,
        "glo_5gb_corporate_7days": 228,
        # MTN SME, GIFTING, DATA SHARE
        "mtn_sme_10gb_monthly_plus": 6,
        "mtn_sme_1gb_7days": 7,
        "mtn_sme_7gb_30days": 8,
        "mtn_sme_11gb_7days": 11,
        "mtn_gifting_1.5gb_7days": 43,
        "mtn_sme_6.75gb_30days": 44,
        "mtn_gifting_500mb_7days": 50,
        "mtn_gifting_1.2gb_social_weekly": 51,
        "mtn_gifting_1gb_1day_plus_1p5min": 52,
        "mtn_gifting_1gb_7days_alt": 208,
        "mtn_gifting_2gb_2days": 209,
        "mtn_gifting_3.2gb_2days": 210,
        "mtn_gifting_2.5gb_2days": 211,
        "mtn_sme_12.5mb_30days": 212,
        "mtn_data_share_1gb_30days": 213,
        "mtn_data_share_2gb_30days": 214,
        "mtn_data_share_3gb_30days": 215,
        "mtn_data_share_5gb_30days": 216,
        "mtn_data_share_500mb_30days": 217,
        "mtn_gifting_500mb_1day": 229,
        "mtn_gifting_7gb_2days": 230,
        "mtn_gifting_2.7gb_30days": 231,
        "mtn_gifting_6gb_7days": 233,
        "mtn_gifting_6.7gb_30days": 234,
        "mtn_gifting_7gb_30days": 235,
        "mtn_gifting_11gb_7days": 236,
        "mtn_gifting_10gb_monthly_plus": 237,
        "mtn_gifting_14.5gb_30days": 238,
        "mtn_gifting_12.5gb_30days": 239,
        "mtn_gifting_20gb_30days": 240,
        "mtn_gifting_500mb_nightplan": 241,
        "mtn_gifting_200mb_2days": 242,
        "mtn_gifting_470mb_social_weekly": 243,
        "mtn_gifting_1gb_ig_tt_yt_weekly": 244,
        "mtn_gifting_2gb_tiktok_weekly": 245,
        "mtn_gifting_110mb_daily": 246,
        "mtn_gifting_2.5gb_1day": 247,
        "mtn_gifting_1.8gb_thryve_7days": 248,
        "mtn_gifting_5gb_thryve_": 249,
        "mtn_sme_3.5gb_30days": 250,
        "mtn_sme_6gb_7days": 251,
        "mtn_sme_2gb_30days": 252,
        "mtn_sme_500mb_7days": 253,
        "mtn_gifting_1.5gb_2days": 285,
        "mtn_gifting_75gb_30days": 286,
        "mtn_gifting_750mb_3days": 287,
    }
    # If not found using .value, fall back to plan.pk if present
    plan = data_purchase.plan

    if plan.value in plan_map:
        return plan_map[plan.value]
    # Sometimes local config does not match, fall back to mapping on id
    if plan.pk in plan_map.values():
        return plan.pk
    raise ValidationError(
        f"Unable to map DataPlan '{plan.value}' (pk={plan.pk}) to an API data plan id."
    )


# Signal to ensure DataPlan objects exist on startup (for dev/test convenience only).

from django.db.models.signals import post_migrate
from django.dispatch import receiver
from app.services.airtime.models import DataPlan, NetworkProvider

# This is a list of example plans to ensure exist in the DB.
# In production, use a management command for full control.
DEFAULT_DATA_PLANS = [
    # 9MOBILE GIFTING plans
    {"provider_label": "9MOBILE", "value": "9mobile_gifting_500mb_30days", "label": "500MB 30 Days (Gifting)", "category": "monthly", "data": "500MB", "amount": 450},
    {"provider_label": "9MOBILE", "value": "9mobile_gifting_1.5gb_30days", "label": "1.5GB 30 Days (Gifting)", "category": "monthly", "data": "1.5GB", "amount": 900},
    {"provider_label": "9MOBILE", "value": "9mobile_gifting_2gb_30days", "label": "2GB 30 Days (Gifting)", "category": "monthly", "data": "2GB", "amount": 1080},
    {"provider_label": "9MOBILE", "value": "9mobile_gifting_3gb_30days", "label": "3GB 30 Days (Gifting)", "category": "monthly", "data": "3GB", "amount": 1350},
    {"provider_label": "9MOBILE", "value": "9mobile_gifting_4.5gb_30days", "label": "4.5GB 30 Days (Gifting)", "category": "monthly", "data": "4.5GB", "amount": 1800},
    {"provider_label": "9MOBILE", "value": "9mobile_gifting_11gb_30days", "label": "11GB 30 Days (Gifting)", "category": "monthly", "data": "11GB", "amount": 3600},
    {"provider_label": "9MOBILE", "value": "9mobile_gifting_15gb_30days", "label": "15GB 30 Days (Gifting)", "category": "monthly", "data": "15GB", "amount": 4500},
    {"provider_label": "9MOBILE", "value": "9mobile_gifting_40gb_30days", "label": "40GB 30 Days (Gifting)", "category": "monthly", "data": "40GB", "amount": 9000},
    {"provider_label": "9MOBILE", "value": "9mobile_gifting_75gb_30days", "label": "75GB 30 Days (Gifting)", "category": "monthly", "data": "75GB", "amount": 13500},

    # AIRTEL GIFTING & AWOOF DATA & CORPORATE GIFTING plans
    {"provider_label": "AIRTEL", "value": "airtel_gifting_3.2gb_2days", "label": "3.2GB 2 Days (Gifting)", "category": "weekly", "data": "3.2GB", "amount": 1000},
    {"provider_label": "AIRTEL", "value": "airtel_gifting_2gb_2days", "label": "2GB 2 Days (Gifting)", "category": "weekly", "data": "2GB", "amount": 750},
    {"provider_label": "AIRTEL", "value": "airtel_gifting_5gb_7days", "label": "5GB 7 Days (Gifting)", "category": "weekly", "data": "5GB", "amount": 1550},
    {"provider_label": "AIRTEL", "value": "airtel_gifting_10gb_7days", "label": "10GB 7 Days (Gifting)", "category": "weekly", "data": "10GB", "amount": 3000},
    {"provider_label": "AIRTEL", "value": "airtel_gifting_1gb_social_3days", "label": "1GB Social 3 Days (Gifting)", "category": "weekly", "data": "1GB", "amount": 300},
    {"provider_label": "AIRTEL", "value": "airtel_gifting_8gb_monthly_binge", "label": "8GB Monthly Binge (Gifting)", "category": "monthly", "data": "8GB", "amount": 3000},
    {"provider_label": "AIRTEL", "value": "airtel_gifting_1.5gb_2days", "label": "1.5GB 2 Days (Gifting)", "category": "weekly", "data": "1.5GB", "amount": 650},
    {"provider_label": "AIRTEL", "value": "airtel_gifting_500mb_7days", "label": "500MB 7 Days (Gifting)", "category": "weekly", "data": "500MB", "amount": 485},
    {"provider_label": "AIRTEL", "value": "airtel_gifting_1gb_1day", "label": "1GB 1 Day (Gifting)", "category": "daily", "data": "1GB", "amount": 500},
    {"provider_label": "AIRTEL", "value": "airtel_gifting_1.5gb_social_7days", "label": "1.5GB Social 7 Days (Gifting)", "category": "weekly", "data": "1.5GB", "amount": 550},
    {"provider_label": "AIRTEL", "value": "airtel_gifting_4gb_monthly_binge", "label": "4GB Monthly Binge (Gifting)", "category": "monthly", "data": "4GB", "amount": 2450},
    {"provider_label": "AIRTEL", "value": "airtel_gifting_1gb_7days", "label": "1GB 7 Days (Gifting)", "category": "weekly", "data": "1GB", "amount": 787},
    {"provider_label": "AIRTEL", "value": "airtel_gifting_3.5gb_7days", "label": "3.5GB 7 Days (Gifting)", "category": "weekly", "data": "3.5GB", "amount": 1450},

    # AIRTEL AWOOF DATA
    {"provider_label": "AIRTEL", "value": "airtel_awoof_1gb_3days", "label": "1GB 3 Days (Awoof)", "category": "weekly", "data": "1GB", "amount": 300},
    {"provider_label": "AIRTEL", "value": "airtel_awoof_2gb_1day", "label": "2GB 1 Day (Awoof)", "category": "daily", "data": "2GB", "amount": 500},
    {"provider_label": "AIRTEL", "value": "airtel_awoof_1.5gb_7days", "label": "1.5GB 7 Days (Awoof)", "category": "weekly", "data": "1.5GB", "amount": 520},
    {"provider_label": "AIRTEL", "value": "airtel_awoof_2gb_2days", "label": "2GB 2 Days (Awoof)", "category": "weekly", "data": "2GB", "amount": 600},
    {"provider_label": "AIRTEL", "value": "airtel_awoof_3gb_2days", "label": "3GB 2 Days (Awoof)", "category": "weekly", "data": "3GB", "amount": 760},
    {"provider_label": "AIRTEL", "value": "airtel_awoof_3.2gb_2days", "label": "3.2GB 2 Days (Awoof)", "category": "weekly", "data": "3.2GB", "amount": 1000},
    {"provider_label": "AIRTEL", "value": "airtel_awoof_1.5gb_1day", "label": "1.5GB 1 Day (Awoof)", "category": "daily", "data": "1.5GB", "amount": 400},
    {"provider_label": "AIRTEL", "value": "airtel_awoof_10gb_7days", "label": "10GB 7 Days (Awoof)", "category": "weekly", "data": "10GB", "amount": 3000},
    {"provider_label": "AIRTEL", "value": "airtel_awoof_600mb_2days", "label": "600MB 2 Days (Awoof)", "category": "weekly", "data": "600MB", "amount": 200},
    {"provider_label": "AIRTEL", "value": "airtel_awoof_150mb_1day", "label": "150MB 1 Day (Awoof)", "category": "daily", "data": "150MB", "amount": 50},
    {"provider_label": "AIRTEL", "value": "airtel_awoof_300mb_2days", "label": "300MB 2 Days (Awoof)", "category": "weekly", "data": "300MB", "amount": 100},
    {"provider_label": "AIRTEL", "value": "airtel_awoof_6.5gb_7days", "label": "6.5GB 7 Days (Awoof)", "category": "weekly", "data": "6.5GB", "amount": 1000},
    {"provider_label": "AIRTEL", "value": "airtel_awoof_5gb_7days", "label": "5GB 7 Days (Awoof)", "category": "weekly", "data": "5GB", "amount": 1450},
    {"provider_label": "AIRTEL", "value": "airtel_awoof_7gb_7days", "label": "7GB 7 Days (Awoof)", "category": "weekly", "data": "7GB", "amount": 1950},
    {"provider_label": "AIRTEL", "value": "airtel_awoof_6gb_7days", "label": "6GB 7 Days (Awoof)", "category": "weekly", "data": "6GB", "amount": 2450},
    {"provider_label": "AIRTEL", "value": "airtel_awoof_13gb_30days", "label": "13GB 30 Days (Awoof)", "category": "monthly", "data": "13GB", "amount": 4850},
    {"provider_label": "AIRTEL", "value": "airtel_awoof_18gb_7days", "label": "18GB 7 Days (Awoof)", "category": "weekly", "data": "18GB", "amount": 4850},
    {"provider_label": "AIRTEL", "value": "airtel_awoof_10gb_30days", "label": "10GB 30 Days (Awoof)", "category": "monthly", "data": "10GB", "amount": 3000},

    # AIRTEL CORPORATE GIFTING (listing a few, you can extend as needed)
    {"provider_label": "AIRTEL", "value": "airtel_corp_100mb_daily", "label": "100MB Daily (Corporate Gifting)", "category": "daily", "data": "100MB", "amount": 100},
    {"provider_label": "AIRTEL", "value": "airtel_corp_300mb_daily", "label": "300MB Daily (Corporate Gifting)", "category": "daily", "data": "300MB", "amount": 200},
    {"provider_label": "AIRTEL", "value": "airtel_corp_1gb_30days", "label": "1GB 30 Days (Corporate Gifting)", "category": "monthly", "data": "1GB", "amount": 787},
    {"provider_label": "AIRTEL", "value": "airtel_corp_500mb_7days", "label": "500MB 7 Days (Corporate Gifting)", "category": "weekly", "data": "500MB", "amount": 485},
    {"provider_label": "AIRTEL", "value": "airtel_corp_1.5gb_7days", "label": "1.5GB 7 Days (Corporate Gifting)", "category": "weekly", "data": "1.5GB", "amount": 1000},

    # GLO CORPORATE GIFTING
    {"provider_label": "GLO", "value": "glo_corp_1gb_30days", "label": "1GB 30 Days (Corporate Gifting)", "category": "monthly", "data": "1GB", "amount": 420},
    {"provider_label": "GLO", "value": "glo_corp_2gb_30days", "label": "2GB 30 Days (Corporate Gifting)", "category": "monthly", "data": "2GB", "amount": 840},
    {"provider_label": "GLO", "value": "glo_corp_3gb_30days", "label": "3GB 30 Days (Corporate Gifting)", "category": "monthly", "data": "3GB", "amount": 1260},
    {"provider_label": "GLO", "value": "glo_corp_5gb_30days", "label": "5GB 30 Days (Corporate Gifting)", "category": "monthly", "data": "5GB", "amount": 2100},
    {"provider_label": "GLO", "value": "glo_corp_10gb_30days", "label": "10GB 30 Days (Corporate Gifting)", "category": "monthly", "data": "10GB", "amount": 4200},
    {"provider_label": "GLO", "value": "glo_corp_500mb_30days", "label": "500MB 30 Days (Corporate Gifting)", "category": "monthly", "data": "500MB", "amount": 210},

    # MTN SME & GIFTING & DATA SHARE (listing just a few representative entries; add more as needed)
    {"provider_label": "MTN", "value": "mtn_sme_10gb_monthly_plus", "label": "10GB Monthly plus + 10 min (SME)", "category": "monthly", "data": "10GB", "amount": 4350},
    {"provider_label": "MTN", "value": "mtn_sme_1gb_7days", "label": "1GB 7 Days (SME)", "category": "weekly", "data": "1GB", "amount": 775},
    {"provider_label": "MTN", "value": "mtn_sme_7gb_30days", "label": "7GB 30 Days (SME)", "category": "monthly", "data": "7GB", "amount": 3450},
    {"provider_label": "MTN", "value": "mtn_sme_11gb_7days", "label": "11GB 7 Days (SME)", "category": "weekly", "data": "11GB", "amount": 3400},
    {"provider_label": "MTN", "value": "mtn_gifting_1.5gb_7days", "label": "1.5GB 7 Days (Gifting)", "category": "weekly", "data": "1.5GB", "amount": 955},
    {"provider_label": "MTN", "value": "mtn_gifting_500mb_7days", "label": "500MB 7 Days (Gifting)", "category": "weekly", "data": "500MB", "amount": 485},
    {"provider_label": "MTN", "value": "mtn_gifting_1gb_1day", "label": "1GB 1 Day plus 1.5 Minutes (Gifting)", "category": "daily", "data": "1GB", "amount": 485},
    {"provider_label": "MTN", "value": "mtn_gifting_1gb_7days", "label": "1GB 7 Days (Gifting)", "category": "weekly", "data": "1GB", "amount": 774},
    {"provider_label": "MTN", "value": "mtn_gifting_2gb_2days", "label": "2GB 2 Days (Gifting)", "category": "daily", "data": "2GB", "amount": 720},
    {"provider_label": "MTN", "value": "mtn_gifting_2.5gb_2days", "label": "2.5GB 2 Days (Gifting)", "category": "daily", "data": "2.5GB", "amount": 870},
    {"provider_label": "MTN", "value": "mtn_data_share_1gb_30days", "label": "1GB 30 Days (Data Share)", "category": "monthly", "data": "1GB", "amount": 500},
    {"provider_label": "MTN", "value": "mtn_data_share_2gb_30days", "label": "2GB 30 Days (Data Share)", "category": "monthly", "data": "2GB", "amount": 1000},
    {"provider_label": "MTN", "value": "mtn_data_share_3gb_30days", "label": "3GB 30 Days (Data Share)", "category": "monthly", "data": "3GB", "amount": 1500},

    # Add further plans as needed following the format above
]

@receiver(post_migrate)
def ensure_minimum_data_plans(sender, **kwargs):
    """
    Ensure some DataPlan objects exist for each provider (for dev/testing).
    """
    for plan in DEFAULT_DATA_PLANS:
        provider_obj = NetworkProvider.objects.filter(label__iexact=plan["provider_label"]).first()
        if provider_obj:
            DataPlan.objects.get_or_create(
                provider=provider_obj,
                value=plan["value"],
                defaults={
                    "label": plan["label"],
                    "category": plan["category"],
                    "data": plan["data"],
                    "amount": plan["amount"],
                }
            )


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
        "smile": 5,
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

    # Get plan id as API expects
    from .signals import get_api_plan_id_from_data_purchase
    plan_id = get_api_plan_id_from_data_purchase(instance)

    if not plan_id:
        raise ValidationError("Cannot determine plan id for API")

    payload_dict = {
        "network": str(network_id),
        "plan": str(plan_id),
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
