from django.urls import path
from .views import (
    VerifyMeterView,
    ElectricityBillPayView,
    CableInternetRenewView,
    EducationFeePayView,
    FlutterwaveBillWebhookView,
    BillPaymentStatusView,
)

urlpatterns = [
    path("bills/verify-meter/", VerifyMeterView.as_view(), name="vs-verify-meter"),
    path("bills/pay/", ElectricityBillPayView.as_view(), name="vs-bills-pay"),
    path("cable-internet/renew/", CableInternetRenewView.as_view(), name="vs-cable-renew"),
    path("education-fees/pay/", EducationFeePayView.as_view(), name="vs-education-pay"),
    path("webhook/flutterwave/", FlutterwaveBillWebhookView.as_view(), name="vs-flw-webhook"),
    path("payment/status/", BillPaymentStatusView.as_view(), name="vs-payment-status"),
]
