from django.test import TestCase
from django.contrib.auth import get_user_model
from notification_center.services import create_notification

User = get_user_model()

class NotificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="mazen", password="123456")

    def test_create_notification(self):
        n = create_notification(recipient=self.user, title="T", message="M", notification_type="system")
        self.assertEqual(n.recipient, self.user)
        self.assertEqual(n.title, "T")
        self.assertFalse(n.is_read)
