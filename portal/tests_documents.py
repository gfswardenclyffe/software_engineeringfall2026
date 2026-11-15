import tempfile
from pathlib import Path
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from .models import ClientDocument

class ClientDocumentTests(TestCase):
    def setUp(self):
        self.root = tempfile.TemporaryDirectory()
        self.addCleanup(self.root.cleanup)
        self.override = override_settings(MEDIA_ROOT=self.root.name)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.owner = User.objects.create_user(username="owner", password="ValidPass123!"); 
        self.other = User.objects.create_user(username="other", password="ValidPass123!")

    def upload(self, filename="proof.pdf", content=b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF"):
        return self.client.post(reverse("document_upload"), {
            "title": "Application proof",
            "file": SimpleUploadedFile(filename, content, content_type="application/pdf"),
        })

    def test_auth_required(self):
        self.assertEqual(self.client.get(reverse("document_upload")).status_code, 302)
        self.assertEqual(self.client.post(reverse("document_upload")).status_code, 302)

    def test_upload_list_download_and_private_storage(self):
        self.client.force_login(self.owner)
        response = self.upload()
        self.assertRedirects(response, reverse("dashboard") + "#documents", fetch_redirect_response=False)
        doc = ClientDocument.objects.get()
        self.assertEqual(doc.owner, self.owner)
        self.assertTrue(Path(doc.file.path).is_file())
        self.assertTrue(str(doc.file.path).startswith(self.root.name))
        index = self.client.get(reverse("dashboard"))
        self.assertContains(index, "Application proof")
        response = self.client.get(reverse("document_download", args=[doc.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content)[:5], b"%PDF-")
        self.assertIn("attachment", response["Content-Disposition"])

    def test_other_user_cannot_view_or_download(self):
        self.client.force_login(self.owner)
        self.upload()
        doc = ClientDocument.objects.get()
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(reverse("dashboard")), "Application proof")
        self.assertEqual(self.client.get(reverse("document_download", args=[doc.pk])).status_code, 404)

    def test_rejects_non_pdf_and_fake_pdf(self):
        self.client.force_login(self.owner)
        for name, content in [("notes.txt", b"hello"), ("fake.pdf", b"hello")]:
            response = self.upload(name, content)
            self.assertEqual(response.status_code, 200)
        self.assertEqual(ClientDocument.objects.count(), 0)

    def test_rejects_oversize(self):
        self.client.force_login(self.owner)
        response = self.upload(content=b"%PDF-" + b"x" * (10 * 1024 * 1024))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ClientDocument.objects.count(), 0)
