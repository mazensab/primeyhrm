from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from notification_center.models import (
    Notification,
    NotificationChannel,
    NotificationDelivery,
    NotificationDeliveryStatus,
    NotificationEvent,
)
from notification_center.services import create_notification

User = get_user_model()


class NotificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="mazen",
            password="123456",
            email="mazen@example.com",
        )
        self.user.mobile_number = "+966500000001"

    def test_create_notification(self):
        n = create_notification(
            recipient=self.user,
            title="T",
            message="M",
            notification_type="system",
        )

        self.assertIsNotNone(n)
        self.assertEqual(n.recipient, self.user)
        self.assertEqual(n.title, "T")
        self.assertEqual(n.message, "M")
        self.assertFalse(n.is_read)

        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(NotificationEvent.objects.count(), 1)
        self.assertEqual(NotificationDelivery.objects.count(), 1)

        event = NotificationEvent.objects.first()
        delivery = NotificationDelivery.objects.first()

        self.assertEqual(n.event, event)
        self.assertEqual(event.target_user, self.user)
        self.assertEqual(event.event_code, "system")
        self.assertEqual(event.event_group, "system")

        self.assertEqual(delivery.event, event)
        self.assertEqual(delivery.notification, n)
        self.assertEqual(delivery.recipient, self.user)
        self.assertEqual(delivery.channel, NotificationChannel.IN_APP)
        self.assertEqual(delivery.status, NotificationDeliveryStatus.SENT)

    @override_settings(
        EMAIL_NOTIFICATIONS_ENABLED=True,
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="info@example.com",
    )
    def test_create_notification_with_email_creates_email_delivery(self):
        n = create_notification(
            recipient=self.user,
            title="Email Title",
            message="Email Body",
            notification_type="system",
            send_email=True,
        )

        self.assertIsNotNone(n)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(NotificationEvent.objects.count(), 1)
        self.assertEqual(NotificationDelivery.objects.count(), 2)

        event = NotificationEvent.objects.first()
        deliveries = NotificationDelivery.objects.filter(event=event).order_by("id")

        self.assertEqual(deliveries.count(), 2)

        in_app_delivery = deliveries.filter(channel=NotificationChannel.IN_APP).first()
        email_delivery = deliveries.filter(channel=NotificationChannel.EMAIL).first()

        self.assertIsNotNone(in_app_delivery)
        self.assertIsNotNone(email_delivery)

        self.assertEqual(in_app_delivery.status, NotificationDeliveryStatus.SENT)
        self.assertEqual(email_delivery.status, NotificationDeliveryStatus.SENT)
        self.assertEqual(email_delivery.destination, self.user.email)
        self.assertEqual(email_delivery.notification, n)

    @patch("whatsapp_center.services.send_notification_center_whatsapp_delivery")
    @override_settings(WHATSAPP_NOTIFICATIONS_ENABLED=True)
    def test_create_notification_with_whatsapp_creates_whatsapp_delivery(
        self,
        mock_send_whatsapp,
    ):
        mock_send_whatsapp.return_value = type(
            "MockWhatsAppLog",
            (),
            {
                "id": 999,
                "delivery_status": "SENT",
                "external_message_id": "wamid.test.123",
                "provider_status": "sent",
                "failure_reason": "",
            },
        )()

        n = create_notification(
            recipient=self.user,
            title="WhatsApp Title",
            message="WhatsApp Body",
            notification_type="system",
            send_whatsapp=True,
            whatsapp_phone="+966500000001",
            whatsapp_recipient_name="Mazen",
            whatsapp_recipient_role="user",
        )

        self.assertIsNotNone(n)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(NotificationEvent.objects.count(), 1)
        self.assertEqual(NotificationDelivery.objects.count(), 2)

        event = NotificationEvent.objects.first()
        deliveries = NotificationDelivery.objects.filter(event=event).order_by("id")

        self.assertEqual(deliveries.count(), 2)

        in_app_delivery = deliveries.filter(channel=NotificationChannel.IN_APP).first()
        whatsapp_delivery = deliveries.filter(channel=NotificationChannel.WHATSAPP).first()

        self.assertIsNotNone(in_app_delivery)
        self.assertIsNotNone(whatsapp_delivery)

        self.assertEqual(in_app_delivery.status, NotificationDeliveryStatus.SENT)
        self.assertEqual(whatsapp_delivery.status, NotificationDeliveryStatus.SENT)
        self.assertEqual(whatsapp_delivery.destination, "+966500000001")
        self.assertEqual(whatsapp_delivery.notification, n)
        self.assertEqual(whatsapp_delivery.provider_name, "whatsapp_center")
        self.assertEqual(whatsapp_delivery.provider_message_id, "wamid.test.123")

        mock_send_whatsapp.assert_called_once()

    @override_settings(WHATSAPP_NOTIFICATIONS_ENABLED=False)
    def test_create_notification_with_whatsapp_disabled_marks_delivery_failed(self):
        n = create_notification(
            recipient=self.user,
            title="WhatsApp Disabled",
            message="Body",
            notification_type="system",
            send_whatsapp=True,
            whatsapp_phone="+966500000001",
        )

        self.assertIsNotNone(n)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(NotificationEvent.objects.count(), 1)
        self.assertEqual(NotificationDelivery.objects.count(), 2)

        event = NotificationEvent.objects.first()
        whatsapp_delivery = NotificationDelivery.objects.filter(
            event=event,
            channel=NotificationChannel.WHATSAPP,
        ).first()

        self.assertIsNotNone(whatsapp_delivery)
        self.assertEqual(whatsapp_delivery.status, NotificationDeliveryStatus.FAILED)

    def test_create_notification_without_recipient_returns_none(self):
        n = create_notification(
            recipient=None,
            title="T",
            message="M",
            notification_type="system",
        )

        self.assertIsNone(n)
        self.assertEqual(Notification.objects.count(), 0)
        self.assertEqual(NotificationEvent.objects.count(), 0)
        self.assertEqual(NotificationDelivery.objects.count(), 0)

    def test_create_notification_empty_title_and_message_returns_none(self):
        n = create_notification(
            recipient=self.user,
            title="",
            message="",
            notification_type="system",
        )

        self.assertIsNone(n)
        self.assertEqual(Notification.objects.count(), 0)
        self.assertEqual(NotificationEvent.objects.count(), 0)
        self.assertEqual(NotificationDelivery.objects.count(), 0)

    def test_mark_notification_as_read(self):
        n = create_notification(
            recipient=self.user,
            title="Read Test",
            message="Read Body",
            notification_type="system",
        )

        self.assertFalse(n.is_read)
        self.assertIsNone(n.read_at)

        n.mark_as_read()
        n.refresh_from_db()

        self.assertTrue(n.is_read)
        self.assertIsNotNone(n.read_at)