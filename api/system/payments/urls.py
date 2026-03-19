from django.urls import path

from .payments_list import list_payments
from .payments_views import latest_payments
from .payments_summary import revenue_summary
from .payments_detail import payment_detail
from .tamara_create_checkout import tamara_create_checkout
from .tamara_webhook import tamara_webhook
from .tap_create_checkout import tap_create_checkout
from .tap_webhook import tap_webhook
from .tap_success_lookup import tap_success_lookup

urlpatterns = [

    path(
        "",
        list_payments,
        name="system_payments_list",
    ),

    path(
        "latest/",
        latest_payments,
        name="system_latest_payments",
    ),

    path(
        "revenue-summary/",
        revenue_summary,
        name="system_revenue_summary",
    ),

    path(
        "tamara/create-checkout/",
        tamara_create_checkout,
        name="tamara_create_checkout",
    ),

    path(
        "tamara/webhook/",
        tamara_webhook,
        name="tamara_webhook",
    ),

    path(
        "tap/create-checkout/",
        tap_create_checkout,
        name="tap_create_checkout",
    ),

    path(
        "tap/webhook/",
        tap_webhook,
        name="tap_webhook",
    ),

    path(
        "tap/success-lookup/",
        tap_success_lookup,
        name="tap_success_lookup",
    ),

    path(
        "<int:payment_id>/",
        payment_detail,
        name="system_payment_detail",
    ),

]