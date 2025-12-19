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

from django.db.models.signals import post_migrate
from app.services.airtime.models import DataPlan, NetworkProvider

# Updated DEFAULT_DATA_PLANS with support for api_platform_id for data plans
DEFAULT_DATA_PLANS = [
    # 9MOBILE GIFTING
    {"id": 182, "provider_label": "9MOBILE", "value": "9mobile_gifting_500mb_30days",
        "label": "500MB 30 Days (Gifting)", "category": "monthly", "data": "500.0MB", "amount": 450},
    {"id": 183, "provider_label": "9MOBILE", "value": "9mobile_gifting_1.5gb_30days",
        "label": "1.5GB 30 Days (Gifting)", "category": "monthly", "data": "1.5GB", "amount": 900},
    {"id": 184, "provider_label": "9MOBILE", "value": "9mobile_gifting_2gb_30days",
        "label": "2.0GB 30 Days (Gifting)", "category": "monthly", "data": "2.0GB", "amount": 1080},
    {"id": 185, "provider_label": "9MOBILE", "value": "9mobile_gifting_3gb_30days",
        "label": "3.0GB 30 Days (Gifting)", "category": "monthly", "data": "3.0GB", "amount": 1350},
    {"id": 186, "provider_label": "9MOBILE", "value": "9mobile_gifting_4.5gb_30days",
        "label": "4.5GB 30 Days (Gifting)", "category": "monthly", "data": "4.5GB", "amount": 1800},
    {"id": 187, "provider_label": "9MOBILE", "value": "9mobile_gifting_11gb_30days",
        "label": "11.0GB 30 Days (Gifting)", "category": "monthly", "data": "11.0GB", "amount": 3600},
    {"id": 188, "provider_label": "9MOBILE", "value": "9mobile_gifting_15gb_30days",
        "label": "15.0GB 30 Days (Gifting)", "category": "monthly", "data": "15.0GB", "amount": 4500},
    {"id": 189, "provider_label": "9MOBILE", "value": "9mobile_gifting_40gb_30days",
        "label": "40.0GB 30 Days (Gifting)", "category": "monthly", "data": "40.0GB", "amount": 9000},
    {"id": 190, "provider_label": "9MOBILE", "value": "9mobile_gifting_75gb_30days",
        "label": "75.0GB 30 Days (Gifting)", "category": "monthly", "data": "75.0GB", "amount": 13500},

    # AIRTEL GIFTING
    {"id": 145, "provider_label": "AIRTEL", "value": "airtel_3.2gb_gifting_2days",
        "label": "3.2GB 2 Days Binge (Gifting)", "category": "weekly", "data": "3.2GB", "amount": 1000},
    {"id": 146, "provider_label": "AIRTEL", "value": "airtel_2gb_gifting_2days",
        "label": "2.0GB 2 Days Binge (Gifting)", "category": "weekly", "data": "2.0GB", "amount": 750},
    {"id": 147, "provider_label": "AIRTEL", "value": "airtel_5gb_gifting_7days",
        "label": "5.0GB 7 Days Binge (Gifting)", "category": "weekly", "data": "5.0GB", "amount": 1550},
    {"id": 148, "provider_label": "AIRTEL", "value": "airtel_10gb_gifting_7days",
        "label": "10.0GB 7 Days Binge (Gifting)", "category": "weekly", "data": "10.0GB", "amount": 3000},
    {"id": 149, "provider_label": "AIRTEL", "value": "airtel_1gb_gifting_social_3days",
        "label": "1.0GB Social 3 Days (Gifting)", "category": "weekly", "data": "1.0GB", "amount": 300},
    {"id": 150, "provider_label": "AIRTEL", "value": "airtel_8gb_gifting_monthlybinge",
        "label": "8.0GB Monthly Binge (Gifting)", "category": "monthly", "data": "8.0GB", "amount": 3000},
    {"id": 163, "provider_label": "AIRTEL", "value": "airtel_1.5gb_gifting_2days",
        "label": "1.5GB 2 Days Binge (Gifting)", "category": "weekly", "data": "1.5GB", "amount": 650},
    {"id": 164, "provider_label": "AIRTEL", "value": "airtel_500mb_gifting_7days",
        "label": "500.0MB 7 Days Binge (Gifting)", "category": "weekly", "data": "500.0MB", "amount": 485},
    {"id": 165, "provider_label": "AIRTEL", "value": "airtel_1gb_gifting_1day",
        "label": "1.0GB 1 Day Binge (Gifting)", "category": "daily", "data": "1.0GB", "amount": 500},
    {"id": 191, "provider_label": "AIRTEL", "value": "airtel_1.5gb_gifting_social_7days",
        "label": "1.5GB Social 7 Days (Gifting)", "category": "weekly", "data": "1.5GB", "amount": 550},
    {"id": 192, "provider_label": "AIRTEL", "value": "airtel_4gb_gifting_monthlybinge",
        "label": "4.0GB Monthly Binge (Gifting)", "category": "monthly", "data": "4.0GB", "amount": 2450},
    {"id": 193, "provider_label": "AIRTEL", "value": "airtel_1gb_gifting_7days",
        "label": "1.0GB 7 Days Binge (Gifting)", "category": "weekly", "data": "1.0GB", "amount": 787},
    {"id": 254, "provider_label": "AIRTEL", "value": "airtel_3.5gb_gifting_7days",
        "label": "3.5GB 7 Days (Gifting)", "category": "weekly", "data": "3.5GB", "amount": 1450},

    # AIRTEL AWOOF DATA
    {"id": 218, "provider_label": "AIRTEL", "value": "airtel_1gb_awoof_3days",
        "label": "1.0GB 3 Days (Awoof Data)", "category": "weekly", "data": "1.0GB", "amount": 300},
    {"id": 219, "provider_label": "AIRTEL", "value": "airtel_2gb_awoof_1day",
        "label": "2.0GB 1 Day (Awoof Data)", "category": "daily", "data": "2.0GB", "amount": 550},
    {"id": 220, "provider_label": "AIRTEL", "value": "airtel_1.5gb_awoof_7days",
        "label": "1.5GB 7 Days (Awoof Data)", "category": "weekly", "data": "1.5GB", "amount": 520},
    {"id": 221, "provider_label": "AIRTEL", "value": "airtel_2gb_awoof_2days",
        "label": "2.0GB 2 Days (Awoof Data)", "category": "weekly", "data": "2.0GB", "amount": 600},
    {"id": 222, "provider_label": "AIRTEL", "value": "airtel_3gb_awoof_2days",
        "label": "3.0GB 2 Days (Awoof Data)", "category": "weekly", "data": "3.0GB", "amount": 760},
    {"id": 273, "provider_label": "AIRTEL", "value": "airtel_3.2gb_awoof_2days",
        "label": "3.2GB 2 Days (Awoof Data)", "category": "weekly", "data": "3.2GB", "amount": 1000},
    {"id": 274, "provider_label": "AIRTEL", "value": "airtel_1.5gb_awoof_1day",
        "label": "1.5GB 1-Day Plan (Awoof Data)", "category": "daily", "data": "1.5GB", "amount": 400},
    {"id": 275, "provider_label": "AIRTEL", "value": "airtel_10gb_awoof_30days",
        "label": "10.0GB 30 Days (Awoof Data)", "category": "monthly", "data": "10.0GB", "amount": 3000},
    {"id": 276, "provider_label": "AIRTEL", "value": "airtel_600mb_awoof_2days",
        "label": "600.0MB 2 Days (Awoof Data)", "category": "weekly", "data": "600.0MB", "amount": 200},
    {"id": 277, "provider_label": "AIRTEL", "value": "airtel_150mb_awoof_1day",
        "label": "150.0MB 1 Day (Awoof Data)", "category": "daily", "data": "150.0MB", "amount": 50},
    {"id": 278, "provider_label": "AIRTEL", "value": "airtel_300mb_awoof_2days",
        "label": "300.0MB 2 Days (Awoof Data)", "category": "weekly", "data": "300.0MB", "amount": 100},
    {"id": 279, "provider_label": "AIRTEL", "value": "airtel_6.5gb_awoof_7days",
        "label": "6.5GB 7 Days (Awoof Data)", "category": "weekly", "data": "6.5GB", "amount": 1000},
    {"id": 280, "provider_label": "AIRTEL", "value": "airtel_5gb_awoof_7days",
        "label": "5.0GB 7 Days (Awoof Data)", "category": "weekly", "data": "5.0GB", "amount": 1450},
    {"id": 281, "provider_label": "AIRTEL", "value": "airtel_7gb_awoof_7days",
        "label": "7.0GB 7 Days (Awoof Data)", "category": "weekly", "data": "7.0GB", "amount": 1950},
    {"id": 282, "provider_label": "AIRTEL", "value": "airtel_6gb_awoof_7days",
        "label": "6.0GB 7 Days (Awoof Data)", "category": "weekly", "data": "6.0GB", "amount": 2450},
    {"id": 283, "provider_label": "AIRTEL", "value": "airtel_13gb_awoof_30days",
        "label": "13.0GB 30 Days (Awoof Data)", "category": "monthly", "data": "13.0GB", "amount": 4850},
    {"id": 284, "provider_label": "AIRTEL", "value": "airtel_18gb_awoof_7days",
        "label": "18.0GB 7 Days (Awoof Data)", "category": "weekly", "data": "18.0GB", "amount": 4850},

    # AIRTEL CORPORATE GIFTING
    {"id": 255, "provider_label": "AIRTEL", "value": "airtel_100mb_corporate_daily",
        "label": "100.0MB Daily plan (Corporate Gifting)", "category": "daily", "data": "100.0MB", "amount": 100},
    {"id": 256, "provider_label": "AIRTEL", "value": "airtel_300mb_corporate_daily",
        "label": "300.0MB Daily plan (Corporate Gifting)", "category": "daily", "data": "300.0MB", "amount": 200},
    {"id": 257, "provider_label": "AIRTEL", "value": "airtel_300mb_corporate_daily_alt",
        "label": "300.0MB Daily plan (Corporate Gifting)", "category": "daily", "data": "300.0MB", "amount": 300},
    {"id": 258, "provider_label": "AIRTEL", "value": "airtel_1gb_corporate_30days",
        "label": "1.0GB 30days [CORPORATE]", "category": "monthly", "data": "1.0GB", "amount": 787},
    {"id": 259, "provider_label": "AIRTEL", "value": "airtel_500mb_corporate_7days",
        "label": "500.0MB 7 Days (Corporate Gifting)", "category": "weekly", "data": "500.0MB", "amount": 485},
    {"id": 260, "provider_label": "AIRTEL", "value": "airtel_1.5gb_corporate_7days",
        "label": "1.5GB 7 Days (Corporate Gifting)", "category": "weekly", "data": "1.5GB", "amount": 1000},
    {"id": 261, "provider_label": "AIRTEL", "value": "airtel_3.5gb_corporate_7days",
        "label": "3.5GB 7 Days (Corporate Gifting)", "category": "weekly", "data": "3.5GB", "amount": 1450},
    {"id": 262, "provider_label": "AIRTEL", "value": "airtel_2gb_corporate_30days",
        "label": "2.0GB 30days [CORPORATE]", "category": "monthly", "data": "2.0GB", "amount": 1450},
    {"id": 264, "provider_label": "AIRTEL", "value": "airtel_3gb_corporate_30days",
        "label": "3.0GB 30days [CORPORATE]", "category": "monthly", "data": "3.0GB", "amount": 1900},
    {"id": 265, "provider_label": "AIRTEL", "value": "airtel_6gb_corporate_7days",
        "label": "6.0GB 7 Days (Corporate Gifting)", "category": "weekly", "data": "6.0GB", "amount": 2450},
    {"id": 266, "provider_label": "AIRTEL", "value": "airtel_4gb_corporate_30days",
        "label": "4.0GB 30days [CORPORATE]", "category": "monthly", "data": "4.0GB", "amount": 2450},
    {"id": 267, "provider_label": "AIRTEL", "value": "airtel_10gb_corporate_7days",
        "label": "10.0GB 7 Days (Corporate Gifting)", "category": "weekly", "data": "10.0GB", "amount": 3000},
    {"id": 268, "provider_label": "AIRTEL", "value": "airtel_8gb_corporate_30days",
        "label": "8.0GB 30days [CORPORATE]", "category": "monthly", "data": "8.0GB", "amount": 2900},
    {"id": 269, "provider_label": "AIRTEL", "value": "airtel_10gb_corporate_30days",
        "label": "10.0GB 30days [CORPORATE]", "category": "monthly", "data": "10.0GB", "amount": 3850},
    {"id": 270, "provider_label": "AIRTEL", "value": "airtel_18gb_corporate_7days",
        "label": "18.0GB 7 Days (Corporate Gifting)", "category": "weekly", "data": "18.0GB", "amount": 5000},
    {"id": 271, "provider_label": "AIRTEL", "value": "airtel_13gb_corporate_30days",
        "label": "13.0GB 30days [CORPORATE]", "category": "monthly", "data": "13.0GB", "amount": 5000},
    {"id": 272, "provider_label": "AIRTEL", "value": "airtel_25gb_corporate_30days",
        "label": "25.0GB 30days [CORPORATE]", "category": "monthly", "data": "25.0GB", "amount": 7850},

    # GLO CORPORATE GIFTING
    {"id": 194, "provider_label": "GLO", "value": "glo_corp_1gb_30days",
        "label": "1.0GB 30days (Corporate Gifting)", "category": "monthly", "data": "1.0GB", "amount": 420},
    {"id": 195, "provider_label": "GLO", "value": "glo_corp_2gb_30days",
        "label": "2.0GB 30days (Corporate Gifting)", "category": "monthly", "data": "2.0GB", "amount": 840},
    {"id": 196, "provider_label": "GLO", "value": "glo_corp_3gb_30days",
        "label": "3.0GB 30days (Corporate Gifting)", "category": "monthly", "data": "3.0GB", "amount": 1260},
    {"id": 197, "provider_label": "GLO", "value": "glo_corp_5gb_30days",
        "label": "5.0GB 30days (Corporate Gifting)", "category": "monthly", "data": "5.0GB", "amount": 2100},
    {"id": 198, "provider_label": "GLO", "value": "glo_corp_10gb_30days",
        "label": "10.0GB 30days (Corporate Gifting)", "category": "monthly", "data": "10.0GB", "amount": 4200},
    {"id": 199, "provider_label": "GLO", "value": "glo_corp_500mb_30days",
        "label": "500.0MB 30 days (Corporate Gifting)", "category": "monthly", "data": "500.0MB", "amount": 210},
    {"id": 206, "provider_label": "GLO", "value": "glo_corp_200mb_30days",
        "label": "200.0MB 30 days (Corporate Gifting)", "category": "monthly", "data": "200.0MB", "amount": 95},
    {"id": 223, "provider_label": "GLO", "value": "glo_corp_1gb_3days",
        "label": "1.0GB 3 Days (Corporate Gifting)", "category": "weekly", "data": "1.0GB", "amount": 270},
    {"id": 224, "provider_label": "GLO", "value": "glo_corp_3gb_3days",
        "label": "3.0GB 3 Days (Corporate Gifting)", "category": "weekly", "data": "3.0GB", "amount": 820},
    {"id": 225, "provider_label": "GLO", "value": "glo_corp_5gb_3days",
        "label": "5.0GB 3 Days (Corporate Gifting)", "category": "weekly", "data": "5.0GB", "amount": 1370},
    {"id": 226, "provider_label": "GLO", "value": "glo_corp_1gb_7days",
        "label": "1.0GB 7 Days (Corporate Gifting)", "category": "weekly", "data": "1.0GB", "amount": 320},
    {"id": 227, "provider_label": "GLO", "value": "glo_corp_3gb_7days",
        "label": "3.0GB 7 Days (Corporate Gifting)", "category": "weekly", "data": "3.0GB", "amount": 930},
    {"id": 228, "provider_label": "GLO", "value": "glo_corp_5gb_7days",
        "label": "5.0GB 7 Days (Corporate Gifting)", "category": "weekly", "data": "5.0GB", "amount": 1550},

    # MTN SME, GIFTING, DATA SHARE
    {"id": 6,   "provider_label": "MTN", "value": "mtn_sme_10gb_monthly_plus",
        "label": "10.0GB Monthly plus + 10 minutes (SME)", "category": "monthly", "data": "10.0GB", "amount": 4350},
    {"id": 7,   "provider_label": "MTN", "value": "mtn_sme_1gb_7days",
        "label": "1.0GB 7 Days (SME)", "category": "weekly", "data": "1.0GB", "amount": 775},
    {"id": 8,   "provider_label": "MTN", "value": "mtn_sme_7gb_30days",
        "label": "7.0GB 30 Days (SME)", "category": "monthly", "data": "7.0GB", "amount": 3450},
    {"id": 11,  "provider_label": "MTN", "value": "mtn_sme_11gb_7days",
        "label": "11.0GB 7 Days (SME)", "category": "weekly", "data": "11.0GB", "amount": 3400},
    {"id": 43,  "provider_label": "MTN", "value": "mtn_gifting_1.5gb_7days",
        "label": "1.5GB 7 Days (Gifting)", "category": "weekly", "data": "1.5GB", "amount": 955},
    {"id": 44,  "provider_label": "MTN", "value": "mtn_sme_6.75gb_30days",
        "label": "6.75GB 30 Days (SME)", "category": "monthly", "data": "6.75GB", "amount": 2900},
    {"id": 50,  "provider_label": "MTN", "value": "mtn_gifting_500mb_7days",
        "label": "500.0MB 7 Days (Gifting)", "category": "weekly", "data": "500.0MB", "amount": 485},
    {"id": 51,  "provider_label": "MTN", "value": "mtn_gifting_1.2gb_social_weekly",
        "label": "1.2GB All Social weekly (Gifting)", "category": "weekly", "data": "1.2GB", "amount": 435},
    {"id": 52,  "provider_label": "MTN", "value": "mtn_gifting_1gb_1day_plus_1p5min",
        "label": "1.0GB 1 Day plus 1.5 Minutes (Gifting)", "category": "daily", "data": "1.0GB", "amount": 485},
    {"id": 208, "provider_label": "MTN", "value": "mtn_gifting_1gb_7days_alt",
        "label": "1.0GB 7 Days (Gifting)", "category": "weekly", "data": "1.0GB", "amount": 774},
    {"id": 209, "provider_label": "MTN", "value": "mtn_gifting_2gb_2days",
        "label": "2.0GB 2 Days (Gifting)", "category": "daily", "data": "2.0GB", "amount": 720},
    {"id": 210, "provider_label": "MTN", "value": "mtn_gifting_3.2gb_2days",
        "label": "3.2GB 2 Days (Gifting)", "category": "daily", "data": "3.2GB", "amount": 960},
    {"id": 211, "provider_label": "MTN", "value": "mtn_gifting_2.5gb_2days",
        "label": "2.5GB 2 Days (Gifting)", "category": "daily", "data": "2.5GB", "amount": 870},
    {"id": 212, "provider_label": "MTN", "value": "mtn_sme_12.5mb_30days",
        "label": "12.5MB 30 Days (SME)", "category": "monthly", "data": "12.5MB", "amount": 5280},
    {"id": 213, "provider_label": "MTN", "value": "mtn_data_share_1gb_30days",
        "label": "1.0GB 30 Days (Data Share)", "category": "monthly", "data": "1.0GB", "amount": 500},
    {"id": 214, "provider_label": "MTN", "value": "mtn_data_share_2gb_30days",
        "label": "2.0GB 30 Days (Data Share)", "category": "monthly", "data": "2.0GB", "amount": 1000},
    {"id": 215, "provider_label": "MTN", "value": "mtn_data_share_3gb_30days",
        "label": "3.0GB 30 Days (Data Share)", "category": "monthly", "data": "3.0GB", "amount": 1500},
    {"id": 216, "provider_label": "MTN", "value": "mtn_data_share_5gb_30days",
        "label": "5.0GB 30 Days (Data Share)", "category": "monthly", "data": "5.0GB", "amount": 2500},
    {"id": 217, "provider_label": "MTN", "value": "mtn_data_share_500mb_30days",
        "label": "500.0MB 30 Days (Data Share)", "category": "monthly", "data": "500.0MB", "amount": 400},
    {"id": 229, "provider_label": "MTN", "value": "mtn_gifting_500mb_1day",
        "label": "500.0MB 1-Day Plan (Gifting)", "category": "daily", "data": "500.0MB", "amount": 350},
    {"id": 230, "provider_label": "MTN", "value": "mtn_gifting_7gb_2days",
        "label": "7.0GB 2 Days (Gifting)", "category": "daily", "data": "7.0GB", "amount": 1800},
    {"id": 231, "provider_label": "MTN", "value": "mtn_gifting_2.7gb_30days",
        "label": "2.7GB 30 Days (Gifting)", "category": "monthly", "data": "2.7GB", "amount": 1920},
    {"id": 233, "provider_label": "MTN", "value": "mtn_gifting_6gb_7days",
        "label": "6.0GB 7 Days (Gifting)", "category": "weekly", "data": "6.0GB", "amount": 2450},
    {"id": 234, "provider_label": "MTN", "value": "mtn_gifting_6.7gb_30days",
        "label": "6.7GB 30 Days (Gifting)", "category": "monthly", "data": "6.7GB", "amount": 2900},
    {"id": 235, "provider_label": "MTN", "value": "mtn_gifting_7gb_30days",
        "label": "7.0GB 30 Days (Gifting)", "category": "monthly", "data": "7.0GB", "amount": 3375},
    {"id": 236, "provider_label": "MTN", "value": "mtn_gifting_11gb_7days",
        "label": "11.0GB 7 Days (Gifting)", "category": "weekly", "data": "11.0GB", "amount": 3400},
    {"id": 237, "provider_label": "MTN", "value": "mtn_gifting_10gb_monthly_plus",
        "label": "10.0GB Monthly plus + 10 minutes (Gifting)", "category": "monthly", "data": "10.0GB", "amount": 4350},
    {"id": 238, "provider_label": "MTN", "value": "mtn_gifting_14.5gb_30days",
        "label": "14.5GB 30 Days (Gifting)", "category": "monthly", "data": "14.5GB", "amount": 4800},
    {"id": 239, "provider_label": "MTN", "value": "mtn_gifting_12.5gb_30days",
        "label": "12.5GB 30 Days (Gifting)", "category": "monthly", "data": "12.5GB", "amount": 5280},
    {"id": 240, "provider_label": "MTN", "value": "mtn_gifting_20gb_30days",
        "label": "20.0GB 30 Days (Gifting)", "category": "monthly", "data": "20.0GB", "amount": 7250},
    {"id": 241, "provider_label": "MTN", "value": "mtn_gifting_500mb_nightplan",
        "label": "500.0MB All Social Night plan (Gifting)", "category": "night", "data": "500.0MB", "amount": 80},
    {"id": 242, "provider_label": "MTN", "value": "mtn_gifting_200mb_2days",
        "label": "200.0MB 2 Days (Gifting)", "category": "daily", "data": "200.0MB", "amount": 195},
    {"id": 243, "provider_label": "MTN", "value": "mtn_gifting_470mb_social_weekly",
        "label": "470.0MB All Social weekly (Gifting)", "category": "weekly", "data": "470.0MB", "amount": 195},
    {"id": 244, "provider_label": "MTN", "value": "mtn_gifting_1gb_ig_tt_yt_weekly",
        "label": "1.0GB IG/TT/YT Weekly (Awoof Data)", "category": "weekly", "data": "1.0GB", "amount": 350},
    {"id": 245, "provider_label": "MTN", "value": "mtn_gifting_2gb_tiktok_weekly",
        "label": "2.0GB TIKTOK WEEKLY PLAN (Awoof Data)", "category": "weekly", "data": "2.0GB", "amount": 450},
    {"id": 246, "provider_label": "MTN", "value": "mtn_gifting_110mb_daily",
        "label": "110.0MB Daily plan (Gifting)", "category": "daily", "data": "110.0MB", "amount": 98},
    {"id": 247, "provider_label": "MTN", "value": "mtn_gifting_2.5gb_1day",
        "label": "2.5GB 1-Day Plan (Gifting)", "category": "daily", "data": "2.5GB", "amount": 750},
    {"id": 248, "provider_label": "MTN", "value": "mtn_gifting_1.8gb_thryve_7days",
        "label": "1.8GB Thryve data + 35M [7days] (Gifting)", "category": "weekly", "data": "1.8GB", "amount": 1445},
    {"id": 249, "provider_label": "MTN", "value": "mtn_gifting_5gb_thryve_",
        "label": "5.0GB Thryve data (Gifting)", "category": "monthly", "data": "5.0GB", "amount": 2900},
    {"id": 250, "provider_label": "MTN", "value": "mtn_sme_3.5gb_30days",
        "label": "3.5GB 30 Days (SME)", "category": "monthly", "data": "3.5GB", "amount": 2450},
    {"id": 251, "provider_label": "MTN", "value": "mtn_sme_6gb_7days",
        "label": "6.0GB 7 Days (SME)", "category": "weekly", "data": "6.0GB", "amount": 2450},
    {"id": 252, "provider_label": "MTN", "value": "mtn_sme_2gb_30days",
        "label": "2.0GB 30 Days (SME)", "category": "monthly", "data": "2.0GB", "amount": 1450},
    {"id": 253, "provider_label": "MTN", "value": "mtn_sme_500mb_7days",
        "label": "500.0MB 7 Days (SME)", "category": "weekly", "data": "500.0MB", "amount": 485},
    {"id": 285, "provider_label": "MTN", "value": "mtn_gifting_1.5gb_2days",
        "label": "1.5GB 2 Days (Gifting)", "category": "daily", "data": "1.5GB", "amount": 582},
    {"id": 286, "provider_label": "MTN", "value": "mtn_gifting_75gb_30days",
        "label": "75.0GB 30 Days (Gifting)", "category": "monthly", "data": "75.0GB", "amount": 18000},
    {"id": 287, "provider_label": "MTN", "value": "mtn_gifting_750mb_3days",
        "label": "750.0MB 3 Days (Gifting)", "category": "weekly", "data": "750.0MB", "amount": 450},
    {"id": 288, "provider_label": "MTN", "value": "mtn_awoof_1mb_daily",
        "label": "1.0MB Awoof Daily plan", "category": "daily", "data": "1.0MB", "amount": 250},
    {"id": 289, "provider_label": "MTN", "value": "mtn_awoof_2.5gb_daily",
        "label": "2.5GB Awoof Daily plan", "category": "daily", "data": "2.5GB", "amount": 550},
]
# Truncated for brevity; rest of plans remain same and will pass through below


@receiver(post_migrate)
def ensure_minimum_data_plans(sender, **kwargs):
    """
    Ensure some example DataPlan objects exist per provider (dev/test use).
    Set api_platform_id to the plan "id" if present.
    """
    for plan in DEFAULT_DATA_PLANS:
        provider_obj = NetworkProvider.objects.filter(
            label__iexact=plan["provider_label"]).first()
        if provider_obj:
            DataPlan.objects.get_or_create(
                provider=provider_obj,
                value=plan["value"],
                defaults={
                    "label": plan["label"],
                    "category": plan["category"],
                    "data": plan["data"],
                    "amount": plan["amount"],
                    # Set the data platform id here
                    "api_platform_id": plan.get("id"),
                }
            )


def get_wallet_and_validate_balance(user, amount, purchase_type="purchase"):
    try:
        wallet = Wallet.objects.get(user=user)
    except Wallet.DoesNotExist:
        raise ValidationError("Wallet does not exist for the user.")
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    if wallet.balance < amount:
        raise ValidationError(
            f"Insufficient wallet balance to complete this {purchase_type}.")
    return wallet, amount


def call_maskawa_api_for_airtime(instance, api_key):
    provider = instance.provider
    network_code = getattr(provider, "value", None)
    if not network_code:
        raise ValidationError("Cannot determine provider code for API")
    provider_code_to_id = {
        "mtn": 1, "glo": 2, "9mobile": 3, "airtel": 4, "smile": 5,
    }
    network_id = provider_code_to_id.get(str(network_code).strip().lower())
    if not network_id:
        raise ValidationError(
            f"Unknown provider code '{network_code}' for Maskawa API")
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
        response = requests.post(url, headers=headers,
                                 data=payload, timeout=20)
    except Exception as e:
        raise ValidationError(
            f"Airtime purchase API request could not be completed: {str(e)}")
    return response


def call_maskawa_api_for_data(instance, api_key):
    provider = instance.provider
    network_code = getattr(provider, "value", None)
    if not network_code:
        raise ValidationError("Cannot determine provider code for API")
    provider_code_to_id = {
        "mtn": 1, "glo": 2, "9mobile": 3, "airtel": 4,
    }
    network_id = provider_code_to_id.get(str(network_code).strip().lower())
    if not network_id:
        raise ValidationError(
            f"Unknown provider code '{network_code}' for Maskawa API")
    plan = instance.plan
    plan_id = getattr(plan, 'api_platform_id', None)
    if not plan_id:
        raise ValidationError(
            "Cannot determine plan id for API (api_platform_id not set on DataPlan)")

    url = "https://premiumsub.com.ng/api/data/"
    # Adapt prompt structure: assign network_id and plan_id directly (not as strings), Ported_number True, no datatype/data
    # Set phone from the instance
    payload = json.dumps({
        "network": network_id,
        "mobile_number": instance.phone,
        "plan": plan_id,
        "Ported_number": True
    })
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
    except Exception as e:
        raise ValidationError(
            f"Data purchase API request could not be completed: {str(e)}")
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
    except Exception:
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
        raise ValidationError(
            f"Provider: {purchase_type.capitalize()} failed: {api_error_message}")
    provider_ref = (
        (maskawa_resp.get("data") or {}).get("reference")
        or maskawa_resp.get("reference")
        or maskawa_resp.get("provider_ref")
        or (maskawa_resp.get("data") or {}).get("ident")
        or maskawa_resp.get("ident")
    )
    if not provider_ref:
        raise ValidationError(
            f"Provider did not return a valid reference for this {purchase_type}.")
    instance.external_ref = provider_ref
    instance.status_message = str(maskawa_resp)
    instance.completed = True


@receiver(pre_save, sender=AirtimePurchase)
def process_airtime_and_validate_wallet(sender, instance, **kwargs):
    user = instance.user
    wallet, amount = get_wallet_and_validate_balance(
        user, instance.amount, "airtime purchase")
    if not instance.external_ref:
        api_key = getattr(settings, "MASKAWA_API_KEY", None)
        if not api_key:
            raise ValidationError(
                "No API key configured for Maskawa provider.")
        response = call_maskawa_api_for_airtime(instance, api_key)
        handle_provider_response(instance, response, "airtime purchase")


@receiver(post_save, sender=AirtimePurchase)
def create_wallet_transaction_for_airtime(sender, instance, created, **kwargs):
    if instance.completed:
        reference = f"airtime-{instance.pk}"
        existing = WalletTransaction.objects.filter(
            reference=reference).first()
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


@receiver(pre_save, sender=DataPurchase)
def process_dataplan_and_validate_wallet(sender, instance, **kwargs):
    user = instance.user
    wallet, amount = get_wallet_and_validate_balance(
        user, instance.amount, "data plan purchase")
    if not instance.external_ref:
        api_key = getattr(settings, "MASKAWA_API_KEY", None)
        if not api_key:
            raise ValidationError(
                "No API key configured for Maskawa provider.")
        response = call_maskawa_api_for_data(instance, api_key)
        handle_provider_response(instance, response, "data plan purchase")


@receiver(post_save, sender=DataPurchase)
def create_wallet_transaction_for_dataplan(sender, instance, created, **kwargs):
    if instance.completed:
        reference = f"data-{instance.pk}"
        existing = WalletTransaction.objects.filter(
            reference=reference).first()
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
