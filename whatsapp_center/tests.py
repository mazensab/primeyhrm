# ============================================================
# 📂 whatsapp_center/tests.py
# Primey HR Cloud - WhatsApp Center Tests
# ============================================================

from django.test import TestCase

from .utils import is_valid_phone_number, normalize_phone_number


class WhatsAppUtilsTests(TestCase):
    def test_normalize_phone_number(self):
        self.assertEqual(normalize_phone_number("00966555555555"), "+966555555555")
        self.assertEqual(normalize_phone_number("966555555555"), "+966555555555")
        self.assertEqual(normalize_phone_number("+966555555555"), "+966555555555")
        self.assertEqual(normalize_phone_number(" 966 55 555 5555 "), "+966555555555")

    def test_is_valid_phone_number(self):
        self.assertTrue(is_valid_phone_number("+966555555555"))
        self.assertTrue(is_valid_phone_number("966555555555"))
        self.assertFalse(is_valid_phone_number("055555"))
        self.assertFalse(is_valid_phone_number(""))