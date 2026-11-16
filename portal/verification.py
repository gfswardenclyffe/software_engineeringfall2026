from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.html import escape
from django.conf import settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.urls import reverse


def send_activation_email(request, user):
    """Send a one-use email confirmation link. Never log the token."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    path = reverse("activate_account", kwargs={"uidb64": uid, "token": token})
    link = request.build_absolute_uri(path)
    if not request.is_secure() and not settings.DEBUG:
        raise RuntimeError("Account verification requires HTTPS.")
    body = (
        "Hello {name},\n\nConfirm your email address to activate your Galiel account:\n{link}\n\n"
        "This link expires in 24 hours. If you did not register, ignore this message.\n\n"
        "Galiel by Wardenclyffe"
    ).format(name=user.first_name or "there", link=link)
    html = (
        '<div style="background:#F2F1EC;padding:30px;font:15px Arial,sans-serif;color:#161616">'
        '<section style="max-width:580px;margin:auto;background:white;border:1px solid #161616;padding:28px">'
        '<p><img src="https://galiel.wardenclyffefirm.com/brand/galiel-signature.png" width="96" height="60" alt="Galiel">'
        '<strong style="font:700 11px Arial;letter-spacing:2px">by WARDENCLYFFE</strong></p>'
        '<h1 style="font:800 25px Arial,sans-serif">Confirm your email address</h1>'
        '<p>Hello ' + escape(user.first_name or "there") + ',</p>'
        '<p>Confirm your email address to activate your Galiel account.</p>'
        '<p><a href="' + escape(link) + '" style="display:inline-block;padding:13px 20px;background:#D9714A;color:#161616;text-decoration:none;border-radius:2px;font-weight:800">Confirm account</a></p>'
        '<p>This link expires in 24 hours. If you did not register, ignore this message.</p>'
        '</section></div>'
    )
    return send_mail("Confirm your Galiel account", body, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False, html_message=html)

