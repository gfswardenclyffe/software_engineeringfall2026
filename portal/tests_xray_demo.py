"""Regression coverage for demo-only fixture provisioning."""
import os
import tempfile
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from portal.models import ServiceApplication, ApplicationDocument
from galiel_ops.models import Reminder, Announcement


class XRayDemoCommandTests(TestCase):
    def test_dry_run_creates_nothing(self):
        output = StringIO()
        call_command("galiel_xray_demo", stdout=output)
        self.assertIn("DRY RUN PASS", output.getvalue())
        self.assertFalse(get_user_model().objects.filter(username="galiel-xray-demo-client").exists())

    def test_apply_requires_strong_distinct_passwords(self):
        with patch.dict(os.environ, {"GALIEL_XRAY_CLIENT_PASSWORD": "",
                                     "GALIEL_XRAY_STAFF_PASSWORD": ""}):
            with self.assertRaises(CommandError):
                call_command("galiel_xray_demo", apply=True, stdout=StringIO())

    def test_demo_only_fixtures(self):
        with tempfile.TemporaryDirectory() as media:
            with override_settings(MEDIA_ROOT=media):
                with patch.dict(os.environ, {
                    "GALIEL_XRAY_CLIENT_PASSWORD": "ClientDemo-Strong-2026!x",
                    "GALIEL_XRAY_STAFF_PASSWORD": "StaffDemo-Stronger-2026!y",
                }):
                    out = StringIO()
                    call_command("galiel_xray_demo", apply=True, stdout=out)
            User = get_user_model()
            client = User.objects.get(username="galiel-xray-demo-client")
            staff = User.objects.get(username="galiel-xray-demo-staff")
            self.assertFalse(staff.is_superuser)
            self.assertTrue(staff.is_staff)
            self.assertEqual(ServiceApplication.objects.filter(client=client).count(), 4)
            primary = ServiceApplication.objects.get(client=client, step=3)
            self.assertEqual(primary.events.count(), 2)
            self.assertEqual(primary.conversation.entries.count(), 2)
            self.assertEqual(ApplicationDocument.objects.filter(application=primary).count(), 1)
            self.assertEqual(Reminder.objects.filter(user=client, read_at__isnull=True).count(), 2)
            self.assertEqual(Announcement.objects.filter(title_en__startswith="Demo:").count(), 3)
            self.assertIn("demo_process_id=" + str(primary.pk), out.getvalue())
