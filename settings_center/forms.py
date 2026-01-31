# ============================================================
# 📂 Settings Center — Forms
# 🎨 Version: V12 Ultra Pro — Synced with Singleton Models
# ============================================================

from django import forms
from .models import (
    SettingsGeneral,
    SettingsCompany,
    SettingsBranding,
    SettingsEmail,
    SettingsIntegrations,
    SettingsSecurity,
    SettingsBackups
)

# ============================================================
# ⚙️ 1) General Settings Form
# ============================================================
class GeneralSettingsForm(forms.ModelForm):
    class Meta:
        model = SettingsGeneral
        fields = [
            "system_name",
            "support_email",
            "support_phone",
            "theme_mode",
            "enable_ai_assistant",
        ]
        widgets = {
            "system_name": forms.TextInput(attrs={"class": "form-control rounded-4"}),
            "support_email": forms.EmailInput(attrs={"class": "form-control rounded-4"}),
            "support_phone": forms.TextInput(attrs={"class": "form-control rounded-4"}),
            "theme_mode": forms.Select(attrs={"class": "form-select rounded-4"}),
            "enable_ai_assistant": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


# ============================================================
# 🏢 2) Company Settings Form
# ============================================================
class CompanySettingsForm(forms.ModelForm):
    class Meta:
        model = SettingsCompany
        fields = ["company_name", "tax_number", "address", "logo"]


# ============================================================
# 🎨 3) Branding Settings Form
# ============================================================
class BrandingSettingsForm(forms.ModelForm):
    class Meta:
        model = SettingsBranding
        fields = [
            "theme_color",
            "accent_color",
            "background_style",
            "logo",
            "favicon",
        ]


# ============================================================
# 📧 4) Email Settings Form
# ============================================================
class EmailSettingsForm(forms.ModelForm):
    class Meta:
        model = SettingsEmail
        fields = [
            "smtp_server",
            "smtp_port",
            "use_tls",
            "username",
            "password",
        ]
        widgets = {
            "password": forms.PasswordInput(attrs={"class": "form-control"}),
        }


# ============================================================
# 🔌 5) Integrations Settings Form
# ============================================================
class IntegrationSettingsForm(forms.ModelForm):
    class Meta:
        model = SettingsIntegrations
        fields = [
            "service_name",
            "api_key",
            "base_url",
            "active",
        ]


# ============================================================
# 🔐 6) Security Settings Form
# ============================================================
class SecuritySettingsForm(forms.ModelForm):
    class Meta:
        model = SettingsSecurity
        fields = [
            "enforce_2fa",
            "session_timeout_minutes",
            "password_min_length",
            "allow_password_reuse",
        ]


# ============================================================
# 💾 7) Backups Settings Form
# ============================================================
class BackupsSettingsForm(forms.ModelForm):
    class Meta:
        model = SettingsBackups
        fields = [
            "enable_auto_backup",
            "backup_frequency",
            "last_backup_at",
        ]
