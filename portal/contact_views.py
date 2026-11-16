"""Public contact form: private lead intake, spam protection, branded email and CRM link."""
import hashlib
import hmac
import logging
import re
from pathlib import Path
from datetime import timedelta

from django import forms
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.html import escape
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache

from .models import CatalogService, ContactLead, ClientConversation, ClientMessage, ServiceOffering

logger = logging.getLogger(__name__)
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024
TEAM_EMAIL = "info@wardenclyffefirm.com"
PHONE_CODES = [("+52", "Mexico +52"), ("+1", "United States +1"), ("+33", "France +33")]
MAX_SUBMISSIONS_PER_HOUR = 5

LABELS = {
    "en": {
        "required": "Please complete this field.",
        "email": "Enter a valid email address.",
        "file": "Only valid PDF, JPG and PNG files up to 10 MB are accepted.",
        "consent": "You must accept the privacy notice.",
        "invalid": "Please correct the highlighted fields.",
        "slow": "Too many messages were submitted recently. Please try again later.",
        "sent": "Thanks — we received your message and will reply within 1 business day.",
        "error": "We could not save your message. Please try again.",
    },
    "es": {
        "required": "Completa este campo.",
        "email": "Escribe un correo electrónico válido.",
        "file": "Solo se aceptan archivos PDF, JPG o PNG válidos de hasta 10 MB.",
        "consent": "Debes aceptar el aviso de privacidad.",
        "invalid": "Corrige los campos señalados.",
        "slow": "Se han enviado demasiados mensajes recientemente. Inténtalo más tarde.",
        "sent": "Gracias. Recibimos tu mensaje y responderemos en un día hábil.",
        "error": "No pudimos guardar tu mensaje. Inténtalo de nuevo.",
    },
    "fr": {
        "required": "Veuillez renseigner ce champ.",
        "email": "Saisissez une adresse e-mail valide.",
        "file": "Seuls les fichiers PDF, JPG ou PNG valides de 10 Mo maximum sont acceptés.",
        "consent": "Veuillez accepter la politique de confidentialité.",
        "invalid": "Veuillez corriger les champs indiqués.",
        "slow": "Trop de messages ont été envoyés récemment. Veuillez réessayer plus tard.",
        "sent": "Merci — nous avons reçu votre message et répondrons sous un jour ouvré.",
        "error": "Nous n’avons pas pu enregistrer votre message. Veuillez réessayer.",
    },
}

def _lang(request):
    lang = (request.POST.get("language") or "en").lower()
    return lang if lang in LABELS else "en"


def _valid_attachment(file):
    if not file:
        return
    if file.size > MAX_ATTACHMENT_SIZE or file.size < 4:
        raise forms.ValidationError("Only valid PDF, JPG and PNG files up to 10 MB are accepted.")
    ext = Path(file.name).suffix.lower()
    signature = file.read(12)
    file.seek(0)
    if ext == ".pdf" and signature.startswith(b"%PDF-"):
        return
    if ext == ".png" and signature.startswith(b"\x89PNG\r\n\x1a\n"):
        return
    if ext in (".jpg", ".jpeg") and signature.startswith(b"\xff\xd8\xff"):
        return
    raise forms.ValidationError("Only valid PDF, JPG and PNG files up to 10 MB are accepted.")


class ContactForm(forms.Form):
    full_name = forms.CharField(max_length=180, strip=True)
    email = forms.EmailField(max_length=254)
    phone_code = forms.ChoiceField(choices=PHONE_CODES, required=False)
    phone = forms.CharField(max_length=32, required=False, strip=True)
    country = forms.ChoiceField(choices=ContactLead.COUNTRIES)
    state_city = forms.CharField(max_length=150, strip=True)
    request_type = forms.CharField(max_length=120)
    message = forms.CharField(max_length=5000, strip=True)
    attachment = forms.FileField(required=False)
    privacy_consent = forms.BooleanField(required=True)
    website = forms.CharField(max_length=200, required=False)
    language = forms.ChoiceField(choices=[("en", "EN"), ("es", "ES"), ("fr", "FR")], required=False)

    def clean_phone(self):
        value = self.cleaned_data["phone"]
        if value and not re.fullmatch(r"[0-9() .-]{5,32}", value):
            raise forms.ValidationError("Enter a valid phone number without a country prefix.")
        return value

    def clean_request_type(self):
        value = self.cleaned_data["request_type"]
        if value == "other":
            return value
        if not CatalogService.objects.filter(
            slug=value, offerings__is_published=True,
        ).exists():
            raise forms.ValidationError("Choose one of the listed services or Other.")
        return value

    def clean_attachment(self):
        file = self.cleaned_data.get("attachment")
        _valid_attachment(file)
        return file


def _lead_details(lead):
    return (
        f"Reference: GL-{lead.pk:06d}\n"
        f"Full name: {lead.full_name}\n"
        f"Email: {lead.email}\n"
        f"Phone: {lead.phone_code} {lead.phone or '(not provided)'}\n"
        f"Country: {lead.get_country_display()}\n"
        f"State / city: {lead.state_city}\n"
        f"Type of request: {lead.request_type}\n"
        f"Attachment: {lead.attachment_filename or '(none)'}\n"
        f"Privacy notice accepted: {lead.privacy_consent_at.isoformat()}\n"
        f"Message:\n{lead.message}"
    )


def _send_mail(lead, visitor):
    locale = lead.language if lead.language in LABELS else "en"
    label = {"en": "Your message to Galiel", "es": "Tu mensaje a Galiel", "fr": "Votre message à Galiel"}[locale]
    introduction = {
        "en": "Thanks — we received your message and will reply within 1 business day.",
        "es": "Gracias. Recibimos tu mensaje y responderemos en un día hábil.",
        "fr": "Merci — nous avons reçu votre message et répondrons sous un jour ouvré.",
    }[locale]
    body = f"{introduction}\n\n{_lead_details(lead)}\n\nGaliel by Wardenclyffe"
    logo = '<strong style="font:italic 32px Georgia,serif;color:#211c19">Galiel</strong> <span style="font:12px Arial;color:#211c19">by Wardenclyffe</span>'
    html = (
        '<div style="background:#f6f1ea;padding:32px;color:#211c19;font:15px Arial,sans-serif">'
        '<div style="background:#fffdf9;max-width:610px;margin:auto;padding:30px;border:1px solid #211c19">'
        + logo + '<p style="font-size:18px">' + escape(introduction) + '</p>'
        + '<p style="white-space:pre-wrap;line-height:1.65">' + escape(_lead_details(lead)) + '</p>'
        + '</div></div>'
    )
    if visitor:
        email = EmailMultiAlternatives(
            f"Galiel · {label} · GL-{lead.pk:06d}", body,
            settings.DEFAULT_FROM_EMAIL, [lead.email],
        )
        email.attach_alternative(html, "text/html")
    else:
        email = EmailMultiAlternatives(
            f"New Galiel lead GL-{lead.pk:06d}: {lead.full_name}",
            _lead_details(lead), settings.DEFAULT_FROM_EMAIL,
            [TEAM_EMAIL], reply_to=[lead.email],
        )
        email.attach_alternative(html, "text/html")
        if lead.attachment:
            with lead.attachment.open("rb") as file:
                email.attach(lead.attachment_filename, file.read(), _mime(lead.attachment_filename))
    email.send(fail_silently=False)


def _mime(filename):
    name = filename.lower()
    return "application/pdf" if name.endswith(".pdf") else ("image/png" if name.endswith(".png") else "image/jpeg")


def _record_and_notify(lead):
    failures = []
    for visitor, field in ((True, "visitor_notified"), (False, "team_notified")):
        try:
            _send_mail(lead, visitor)
        except Exception as exc:
            logger.exception("Galiel lead %s: email delivery failure for %s", lead.pk, field)
            failures.append(field + ": " + type(exc).__name__)
        else:
            ContactLead.objects.filter(pk=lead.pk).update(**{field: True})
    if failures:
        ContactLead.objects.filter(pk=lead.pk).update(delivery_error="; ".join(failures))


def _ip_digest(request):
    # Only use the actual REMOTE_ADDR; do not trust arbitrary forwarded headers.
    ip = request.META.get("REMOTE_ADDR", "")
    return hmac.new(settings.SECRET_KEY.encode(), ip.encode(), hashlib.sha256).hexdigest() if ip else ""


@never_cache
@require_POST
def contact_submit(request):
    lang = _lang(request)
    l = LABELS[lang]
    # Shared-hosted Apache's limit may reject payloads before this code.
    if request.META.get("CONTENT_LENGTH", "").isdigit() and int(request.META["CONTENT_LENGTH"]) > MAX_ATTACHMENT_SIZE + 1024 * 1024:
        return JsonResponse({"ok": False, "message": l["file"], "errors": {"attachment": [l["file"]]}}, status=400)

    form = ContactForm(request.POST, request.FILES)
    # Check the honeypot before validating other fields to avoid disclosing bot filters.
    if (request.POST.get("website") or "").strip():
        return JsonResponse({"ok": True, "message": l["sent"]})
    if not form.is_valid():
        errors = form.errors.get_json_data()
        translated = {}
        for field, items in errors.items():
            translated[field] = []
            for item in items:
                msg = item["message"]
                if field == "privacy_consent":
                    msg = l["consent"]
                elif field == "attachment":
                    msg = l["file"]
                elif item.get("code") == "required":
                    msg = l["required"]
                elif field == "email":
                    msg = l["email"]
                translated[field].append(msg)
        return JsonResponse({"ok": False, "message": l["invalid"], "errors": translated}, status=400)

    digest = _ip_digest(request)
    since = timezone.now() - timedelta(hours=1)
    if digest and ContactLead.objects.filter(ip_digest=digest, created_at__gte=since).count() >= MAX_SUBMISSIONS_PER_HOUR:
        return JsonResponse({"ok": False, "message": l["slow"], "errors": {}}, status=429)

    cleaned = form.cleaned_data
    title = ("Other / not listed" if cleaned["request_type"] == "other" else
             CatalogService.objects.get(slug=cleaned["request_type"]).title_en)
    lead = None
    try:
        with transaction.atomic():
            lead = ContactLead(
                full_name=cleaned["full_name"],
                email=cleaned["email"],
                phone_code=cleaned.get("phone_code") or "+52",
                phone=cleaned.get("phone") or "",
                country=cleaned["country"],
                state_city=cleaned["state_city"],
                request_type=title,
                message=cleaned["message"],
                privacy_consent_at=timezone.now(),
                language=lang,
                client=request.user if request.user.is_authenticated else None,
                ip_digest=digest,
            )
            lead.save()
            uploaded = cleaned.get("attachment")
            if uploaded:
                lead.attachment_filename = Path(uploaded.name).name[:255]
                lead.attachment.save(lead.attachment_filename, uploaded, save=False)
                lead.save(update_fields=["attachment", "attachment_filename"])
            if request.user.is_authenticated:
                conversation = ClientConversation.objects.create(
                    client=request.user,
                    subject=f"Contact inquiry GL-{lead.pk:06d}: {title}"[:160],
                )
                ClientMessage.objects.create(
                    conversation=conversation, sender=request.user,
                    body=cleaned["message"],
                )
                lead.conversation = conversation
                lead.save(update_fields=["conversation"])
    except Exception:
        logger.exception("Failed to save Galiel contact submission")
        return JsonResponse({"ok": False, "message": l["error"], "errors": {}}, status=500)

    # Persist the lead first: outbound SMTP failures never lose an inquiry.
    _record_and_notify(lead)
    return JsonResponse({"ok": True, "message": l["sent"], "reference": f"GL-{lead.pk:06d}"})
