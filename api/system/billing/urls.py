from django.urls import path

from api.system.billing_v3 import billing_overview
from api.system.billing.system_invoices import system_invoices
from api.system.billing.invoice_detail import invoice_detail

urlpatterns = [

    path("", billing_overview),

    path("invoices/", system_invoices),

    path(
        "invoices/<int:invoice_id>/",
        invoice_detail,
    ),

]