from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import ClientConversation, ClientMessage


class MessagingTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username="alice", email="alice@example.com", password="StrongPass123!")
        self.bob = User.objects.create_user(username="bob", email="bob@example.com", password="StrongPass123!")
        self.staff = User.objects.create_user(username="staff", email="staff@example.com", password="StrongPass123!", is_staff=True)
        self.superuser = User.objects.create_superuser(username="admin", email="admin@example.com", password="StrongPass123!")

    def new(self, subject="Permit application", body="Hello Wardenclyffe"):
        return self.client.post(reverse("conversation_new"), {"subject": subject, "body": body})

    def test_authentication_required(self):
        for name in ("messages_inbox", "conversation_new"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 302)
        self.assertEqual(self.client.post(reverse("conversation_new"), {"subject": "X", "body": "Hello"}).status_code, 302)

    def test_client_creates_and_reads_conversation(self):
        self.client.force_login(self.alice)
        self.assertRedirects(self.new(), reverse("conversation_detail", args=[1]))
        convo = ClientConversation.objects.get()
        self.assertEqual(convo.client, self.alice)
        self.assertEqual(ClientMessage.objects.count(), 1)
        self.assertEqual(convo.entries.first().sender, self.alice)
        self.assertContains(self.client.get(reverse("messages_inbox")), "Permit application")
        self.assertContains(self.client.get(reverse("conversation_detail", args=[convo.pk])), "Hello Wardenclyffe")
        self.assertContains(self.client.get(reverse("dashboard")), "Permit application")

    def test_client_cannot_read_or_reply_to_other_clients_thread(self):
        self.client.force_login(self.alice)
        self.new(body="Private conversation")
        convo = ClientConversation.objects.get()
        self.client.force_login(self.bob)
        self.assertNotContains(self.client.get(reverse("messages_inbox")), convo.subject)
        url = reverse("conversation_detail", args=[convo.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, {"body": "Intrusion"}).status_code, 404)
        self.assertEqual(ClientMessage.objects.count(), 1)

    def test_staff_can_read_and_reply_but_cannot_create_as_client(self):
        self.client.force_login(self.alice)
        self.new()
        convo = ClientConversation.objects.get()
        self.client.force_login(self.staff)
        self.assertContains(self.client.get(reverse("messages_inbox")), convo.subject)
        self.assertEqual(self.new().status_code, 403)
        response = self.client.post(reverse("conversation_detail", args=[convo.pk]), {"body": "We'll review the documents."})
        self.assertRedirects(response, reverse("conversation_detail", args=[convo.pk]))
        self.assertEqual(ClientMessage.objects.count(), 2)
        self.assertEqual(convo.entries.last().sender, self.staff)
        self.client.force_login(self.alice)
        self.assertContains(self.client.get(reverse("conversation_detail", args=[convo.pk])), "We'll review the documents.")

    def test_superuser_can_read_reply(self):
        self.client.force_login(self.alice)
        self.new()
        convo = ClientConversation.objects.get()
        self.client.force_login(self.superuser)
        self.assertEqual(self.client.get(reverse("conversation_detail", args=[convo.pk])).status_code, 200)

    def test_validation_rejects_blank_messages_and_long_subject(self):
        self.client.force_login(self.alice)
        for subject, body in [(" ", "hello"), ("Subject", "   "), ("x" * 161, "hello")]:
            response = self.new(subject, body)
            self.assertEqual(response.status_code, 200)
        self.assertEqual(ClientConversation.objects.count(), 0)
        self.new()
        convo = ClientConversation.objects.get()
        response = self.client.post(reverse("conversation_detail", args=[convo.pk]), {"body": "  "})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ClientMessage.objects.count(), 1)

    def test_get_does_not_create_thread_and_create_requires_post(self):
        self.client.force_login(self.alice)
        self.assertEqual(self.client.get(reverse("conversation_new")).status_code, 405)
        self.assertEqual(ClientConversation.objects.count(), 0)
