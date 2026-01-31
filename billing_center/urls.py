from django.urls import path
from . import views

urlpatterns = [
    path('', views.billing_dashboard, name='billing_dashboard'),

    path('invoices/', views.billing_invoices, name='billing_invoices'),
    path('invoices/<int:invoice_id>/', views.billing_invoice_detail, name='billing_invoice_detail'),

    path('plans/', views.billing_plans, name='billing_plans'),

    path('subscription/', views.billing_subscription, name='billing_subscription'),
    path('subscription/edit/', views.billing_subscription_edit, name='billing_subscription_edit'),

    path('transactions/', views.billing_transactions, name='billing_transactions'),

    path('dashboard/', views.billing_dashboard, name='billing_dashboard'),

]
