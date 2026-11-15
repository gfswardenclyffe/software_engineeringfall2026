from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
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
    return send_mail(
        "Confirm your Galiel account",
        "Hello {name},\n\nConfirm your email address to activate your Galiel account:\n{link}\n\n"
        "This link expires in 24 hours. If you did not register, ignore this message.\n\n"
        "Galiel by Wardenclyffe".format(name=user.first_name or "there", link=link),
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
