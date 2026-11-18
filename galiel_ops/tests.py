"""Privacy and functional tests against portal's production 0011 schema.

Run: python manage.py test galiel_ops --noinput
No payments, fake clients, or production records are created outside test DB.
"""
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from portal.models import CatalogCountry, CatalogService, ServiceOffering, ServiceApplication
from .models import Announcement, Reminder, AccountDeletionRequest, FiscalProfile, InvoiceRequest

@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class GalielOpsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User=get_user_model()
        cls.alice=User.objects.create_user(username="alice-ops@example.test",email="alice-ops@example.test",password="SafeTestAccount1!")
        cls.bob=User.objects.create_user(username="bob-ops@example.test",email="bob-ops@example.test",password="SafeTestAccount2!")
        cls.staff=User.objects.create_user(username="staff-ops@example.test",email="staff-ops@example.test",password="SafeTestAccount3!",is_staff=True)
        cls.country=CatalogCountry.objects.create(code="MX",name_en="Mexico",name_es="México",name_fr="Mexique")
        cls.service=CatalogService.objects.create(slug="ops-check",title_en="Administrative paperwork",title_es="Trámite",title_fr="Démarche")
        cls.offering=ServiceOffering.objects.create(country=cls.country,service=cls.service,currency="MXN",is_published=True,price_type="quote")
        cls.case_a=ServiceApplication.objects.create(client=cls.alice,offering=cls.offering,status="draft",step=5,service_title="Client A paperwork")
        cls.case_b=ServiceApplication.objects.create(client=cls.bob,offering=cls.offering,status="draft",step=5,service_title="Client B paperwork")
    def test_private_pages_require_login(self):
        for name in ("galiel_announcements","galiel_reminders","galiel_fiscal_profile","galiel_help_processes"):
            res=self.client.get(reverse(name))
            self.assertEqual(res.status_code,302,name)
    def test_expired_and_future_news_hidden(self):
        now=timezone.now()
        for title,when,expiry in [
            ("Current",now-timedelta(hours=2),None),
            ("Expired",now-timedelta(days=3),now-timedelta(days=1)),
            ("Upcoming",now+timedelta(hours=2),None)]:
            Announcement.objects.create(title_en=title,title_es=title,title_fr=title,body_en="Body",body_es="Cuerpo",body_fr="Texte",category="news",published_at=when,expires_at=expiry,author=self.staff)
        self.client.force_login(self.alice)
        page=self.client.get(reverse("galiel_announcements"),{"category":"news","lang":"es"})
        self.assertContains(page,"Current");self.assertNotContains(page,"Expired");self.assertNotContains(page,"Upcoming")
    def test_reminders_isolated_and_post_only(self):
        reminder=Reminder.objects.create(user=self.bob,application=self.case_b,kind="renewal",message="Sensitive Bob notice")
        self.client.force_login(self.alice)
        self.assertNotContains(self.client.get(reverse("galiel_reminders")),"Sensitive Bob notice")
        for name in ("galiel_reminder_read","galiel_reminder_dismiss"):
            self.assertEqual(self.client.get(reverse(name,args=[reminder.pk])).status_code,405)
            self.assertEqual(self.client.post(reverse(name,args=[reminder.pk])).status_code,404)
        self.assertEqual(self.client.get(reverse("galiel_unread_count")).json()["unread"],0)
    def test_read_and_dismiss_own_alert(self):
        r=Reminder.objects.create(user=self.alice,kind="other",message="Personal")
        self.client.force_login(self.alice)
        self.assertEqual(self.client.get(reverse("galiel_unread_count")).json()["unread"],1)
        self.client.post(reverse("galiel_reminder_read",args=[r.pk]))
        self.assertEqual(self.client.get(reverse("galiel_unread_count")).json()["unread"],0)
        self.client.post(reverse("galiel_reminder_dismiss",args=[r.pk]))
        r.refresh_from_db();self.assertTrue(r.dismissed)
    def test_draft_delete_ownership_and_confirmation(self):
        self.client.force_login(self.alice)
        wrong=reverse("galiel_delete_draft",args=[self.case_b.pk])
        self.assertEqual(self.client.post(wrong,{"confirm":self.case_b.number}).status_code,404)
        mine=reverse("galiel_delete_draft",args=[self.case_a.pk])
        self.assertEqual(self.client.post(mine,{"confirm":"no"}).status_code,403)
        self.assertEqual(self.client.post(mine,{"confirm":self.case_a.number}).status_code,302)
        self.assertFalse(ServiceApplication.objects.filter(pk=self.case_a.pk).exists())
        self.assertTrue(ServiceApplication.objects.filter(pk=self.case_b.pk).exists())
    def test_submitted_cannot_delete(self):
        self.case_a.status="submitted";self.case_a.save(update_fields=["status"])
        self.client.force_login(self.alice)
        self.assertEqual(self.client.post(reverse("galiel_delete_draft",args=[self.case_a.pk]),{"confirm":self.case_a.number}).status_code,403)
    def test_fiscal_data_is_private(self):
        self.client.force_login(self.alice)
        data={"rfc":"ABCD990101XYZ","razon_social":"A's company","regimen_fiscal":"601","uso_cfdi":"G03","invoice_email":"invoice@example.test"}
        self.assertEqual(self.client.post(reverse("galiel_fiscal_profile"),data).status_code,302)
        self.client.force_login(self.bob)
        self.assertNotContains(self.client.get(reverse("galiel_fiscal_profile")),"A's company")
        self.assertEqual(FiscalProfile.objects.filter(user=self.alice).count(),1)
    def test_invoice_request_owner_only(self):
        self.client.force_login(self.alice)
        self.assertEqual(self.client.post(reverse("galiel_request_invoice",args=[self.case_b.pk]),{"invoice_requested":"yes"}).status_code,404)
        self.assertEqual(self.client.post(reverse("galiel_request_invoice",args=[self.case_a.pk]),{"invoice_requested":"yes"}).status_code,302)
        self.assertEqual(InvoiceRequest.objects.filter(user=self.alice).count(),1)
    def test_deletion_request_does_not_deactivate_account(self):
        self.client.force_login(self.alice)
        self.assertEqual(self.client.post(reverse("galiel_request_account_deletion")).status_code,302)
        self.assertTrue(get_user_model().objects.get(pk=self.alice.pk).is_active)
        self.assertEqual(AccountDeletionRequest.objects.filter(user=self.alice,status="pending").count(),1)
    def test_help_processes_never_leak_cross_client(self):
        self.client.force_login(self.alice)
        result=self.client.get(reverse("galiel_help_processes"))
        self.assertIn(self.case_a.number,str(result.json()))
        self.assertNotIn(self.case_b.number,str(result.json()))
    def test_status_transition_creates_private_reminder(self):
        self.case_a.status="missing_documents";self.case_a.save(update_fields=["status"])
        self.assertTrue(Reminder.objects.filter(user=self.alice,application=self.case_a,kind="documents").exists())
        self.assertFalse(Reminder.objects.filter(user=self.bob,application=self.case_a).exists())
    def test_client_wizard_and_document_access_is_private(self):
        self.client.force_login(self.alice)
        for step in range(1,7):
            self.assertEqual(self.client.get(reverse("application_step",args=[self.case_b.pk,step])).status_code,404)
        self.assertEqual(self.client.get(reverse("application_track",args=[self.case_b.pk])).status_code,404)
    def test_checkout_retains_existing_payment_hold(self):
        self.client.force_login(self.alice)
        response=self.client.post(reverse("application_checkout",args=[self.case_a.pk]))
        self.assertNotEqual(response.status_code,200)
        self.case_a.refresh_from_db()
        self.assertIsNone(self.case_a.payment_confirmed_at)
