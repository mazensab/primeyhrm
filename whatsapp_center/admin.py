# ============================================================
# 📂 whatsapp_center/admin.py
# Mham Cloud - WhatsApp Center Admin
# ============================================================

from django.contrib import admin

from .models import (
    CompanyWhatsAppConfig,
    SystemWhatsAppConfig,
    WhatsAppBroadcast,
    WhatsAppBroadcastRecipient,
    WhatsAppMessageAttempt,
    WhatsAppMessageLog,
    WhatsAppReminderRule,
    WhatsAppTemplate,
    WhatsAppWebhookEvent,
)


@admin.register(SystemWhatsAppConfig)
class SystemWhatsAppConfigAdmin(admin.ModelAdmin):
    list_display = ("id", "provider", "is_enabled", "is_active", "phone_number", "updated_at")
    list_filter = ("provider", "is_enabled", "is_active")
    search_fields = ("business_name", "phone_number", "phone_number_id")


@admin.register(CompanyWhatsAppConfig)
class CompanyWhatsAppConfigAdmin(admin.ModelAdmin):
    list_display = ("company", "provider", "is_enabled", "is_active", "phone_number", "updated_at")
    list_filter = ("provider", "is_enabled", "is_active")
    search_fields = ("company__name", "display_name", "phone_number", "phone_number_id")


@admin.register(WhatsAppTemplate)
class WhatsAppTemplateAdmin(admin.ModelAdmin):
    list_display = ("id", "scope_type", "company", "event_code", "message_type", "language_code", "version", "is_active")
    list_filter = ("scope_type", "message_type", "language_code", "is_active", "is_default")
    search_fields = ("event_code", "template_key", "template_name", "meta_template_name")


@admin.register(WhatsAppMessageLog)
class WhatsAppMessageLogAdmin(admin.ModelAdmin):
    list_display = ("id", "scope_type", "company", "event_code", "recipient_phone", "message_type", "delivery_status", "created_at")
    list_filter = ("scope_type", "message_type", "delivery_status", "trigger_source")
    search_fields = ("recipient_phone", "recipient_name", "external_message_id", "event_code")
    readonly_fields = ("created_at", "updated_at", "sent_at", "delivered_at", "read_at", "failed_at")


@admin.register(WhatsAppMessageAttempt)
class WhatsAppMessageAttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "message_log", "attempt_number", "status_code", "is_success", "created_at")
    list_filter = ("is_success",)
    search_fields = ("message_log__recipient_phone", "message_log__external_message_id")


@admin.register(WhatsAppWebhookEvent)
class WhatsAppWebhookEventAdmin(admin.ModelAdmin):
    list_display = ("id", "scope_type", "company", "provider", "event_type", "external_message_id", "is_processed", "created_at")
    list_filter = ("scope_type", "provider", "is_processed", "event_type")
    search_fields = ("external_message_id", "event_type")


@admin.register(WhatsAppBroadcast)
class WhatsAppBroadcastAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "audience_type", "message_type", "status", "total_recipients", "sent_count", "failed_count", "created_at")
    list_filter = ("audience_type", "message_type", "status")
    search_fields = ("title",)


@admin.register(WhatsAppBroadcastRecipient)
class WhatsAppBroadcastRecipientAdmin(admin.ModelAdmin):
    list_display = ("id", "broadcast", "recipient_phone", "recipient_type", "delivery_status", "created_at")
    list_filter = ("recipient_type", "delivery_status")
    search_fields = ("recipient_phone", "recipient_name", "external_message_id")


@admin.register(WhatsAppReminderRule)
class WhatsAppReminderRuleAdmin(admin.ModelAdmin):
    list_display = ("id", "scope_type", "event_code", "days_before", "is_active", "updated_at")
    list_filter = ("scope_type", "is_active")
    search_fields = ("event_code",)