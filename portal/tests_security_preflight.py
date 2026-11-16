"""Security preflight tests for the isolated v10 configuration release."""
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse

from wardenclyffe_portal.private_env import load_private_env


class EnvironmentLoaderTests(SimpleTestCase):
    def test_production_missing_private_env_fails_closed(self):
        with patch.dict(os.environ, {"GALIEL_ENV": "production"}):
            with patch("pathlib.Path.home", return_value=Path("/a/nonexistent/galiel-test-home")):
                with self.assertRaises(RuntimeError):
                    load_private_env()

    def test_explicit_development_has_no_private_file_requirement(self):
        with patch.dict(os.environ, {"GALIEL_ENV": "development"}):
            with patch("pathlib.Path.home", side_effect=AssertionError("Must not touch production home")):
                self.assertIsNone(load_private_env())

    def test_security_cookie_defaults(self):
        self.assertTrue(settings.SESSION_COOKIE_SECURE)
        self.assertTrue(settings.CSRF_COOKIE_SECURE)
        self.assertIn("https://galiel.wardenclyffefirm.com", settings.CSRF_TRUSTED_ORIGINS)
        self.assertEqual(settings.SECURE_PROXY_SSL_HEADER, ("HTTP_X_FORWARDED_PROTO", "https"))


class HttpsLoginCsrfPreflightTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="security-preflight@example.test",
            email="security-preflight@example.test",
            password="SecurityPreflightTestPassword123!",
        )

    def test_login_with_real_csrf_and_https_proxy(self):
        client = Client(enforce_csrf_checks=True, HTTP_X_FORWARDED_PROTO="https")
        response = client.get(reverse("login"), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.is_secure())
        token = client.cookies.get("csrftoken")
        self.assertIsNotNone(token)
        response = client.post(
            reverse("login"),
            {"username": self.user.username, "password": "SecurityPreflightTestPassword123!",
             "csrfmiddlewaretoken": token.value},
            secure=True,
            HTTP_REFERER="https://galiel.wardenclyffefirm.com/login/",
        )
        self.assertIn(response.status_code, (302, 303))
        self.assertIn("_auth_user_id", client.session)

    def test_login_without_csrf_token_rejected(self):
        client = Client(enforce_csrf_checks=True, HTTP_X_FORWARDED_PROTO="https")
        response = client.post(
            reverse("login"),
            {"username": self.user.username, "password": "SecurityPreflightTestPassword123!"},
            secure=True,
            HTTP_REFERER="https://galiel.wardenclyffefirm.com/login/",
        )
        self.assertEqual(response.status_code, 403)
