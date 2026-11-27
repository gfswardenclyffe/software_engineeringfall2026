from django.contrib import messages
from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from django.http import FileResponse, Http404, HttpResponseForbidden, JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.db import transaction
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.conf import settings

from .forms import EmailAuthenticationForm, GalielRegistrationForm, UserProfileForm
from .verification import send_activation_email
from .pricing import fee_note
from .models import ClientDocument, ClientConversation, ClientMessage, CatalogCountry, CatalogRegion, CatalogMunicipality, ServiceOffering, ServiceApplication, ApplicationDocument, CatalogService
from .document_forms import ClientDocumentForm
from .message_forms import NewConversationForm, ReplyForm
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


SERVICE_LABELS = {
    "nl-monterrey-licencia-funcionamiento": "Licencia / permiso de funcionamiento · Monterrey",
    "nl-monterrey-uso-suelo": "Uso de suelo · Monterrey",
    "nl-monterrey-construccion": "Licencia de construcción · Monterrey",
    "nl-sanpedro-uso-suelo": "Licencia de uso de suelo · San Pedro Garza García",
    "nl-sanpedro-construccion-nueva": "Construcción de obra nueva · San Pedro Garza García",
    "cdmx-bj-establecimiento": "Establecimiento mercantil · Benito Juárez",
    "cdmx-cuauhtemoc-establecimiento": "Establecimiento mercantil · Cuauhtémoc",
    "qro-qro-funcionamiento": "Licencia de funcionamiento · Santiago de Querétaro",
    "qro-qro-sare": "SARE / apertura rápida · Santiago de Querétaro",
    "jal-gdl-giro-a": "Licencia de giro Tipo A · Guadalajara",
    "col-funcionamiento": "Licencia municipal de funcionamiento · Colima",
    "tam-reynosa-funcionamiento": "Funcionamiento · Reynosa",
    "tx-notarization": "Notarization assistance · Texas",
    "tx-apostille": "Apostille coordination · Texas",
    "tx-translation": "Professional translations · Texas",
    "tx-entity-filing": "Selected business filing · Texas",
    "fr-translation": "Translations · France",
    "fr-apostille-legalization": "Apostille / legalization coordination · France",
    "fr-admin-review": "Administrative process review · France",
}


# This catalog is available inside the authenticated client workspace.
# Service inquiry links do not create requests or payments automatically.
SERVICE_GROUPS = (
    ("Mexico", "Municipal and administrative services", ("nl-", "cdmx-", "qro-", "jal-", "col-", "tam-")),
    ("United States", "Texas services", ("tx-",)),
    ("France", "Administrative assistance", ("fr-",)),
)


def workspace_service_groups():
    return [
        {
            "name": name,
            "description": description,
            "services": [
                {"code": code, "label": label}
                for code, label in SERVICE_LABELS.items()
                if code.startswith(prefixes)
            ],
        }
        for name, description, prefixes in SERVICE_GROUPS
    ]


def _capture_pending_service(request):
    service = (request.GET.get("service") or request.POST.get("service") or "").strip()
    if service in SERVICE_LABELS or (
        service and ServiceOffering.objects.filter(service__slug=service, is_published=True).exists()
    ):
        request.session["pending_service"] = service
    return request.session.get("pending_service", "")


def _pending_service_label(code):
    if not code:
        return ""
    if code in SERVICE_LABELS:
        return SERVICE_LABELS[code]
    match = ServiceOffering.objects.filter(
        service__slug=code, is_published=True,
    ).select_related("service").first()
    return match.service.title_en if match else code.replace("-", " ").title()


class ServiceAwareLoginView(LoginView):
    template_name = "portal/login.html"
    authentication_form = EmailAuthenticationForm

    def dispatch(self, request, *args, **kwargs):
        _capture_pending_service(request)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        code = self.request.session.get("pending_service", "")
        context["pending_service"] = code
        context["pending_service_label"] = _pending_service_label(code)
        return context

    def get_success_url(self):
        # Respect Django's validated ?next= parameter after login.
        safe_next = self.get_redirect_url()
        if safe_next:
            return safe_next
        code = self.request.session.get("pending_service", "")
        if code:
            return reverse("service_start")
        return reverse("dashboard")


def home(request):
    published = ServiceOffering.objects.filter(is_published=True)
    regions = list(CatalogRegion.objects.filter(
        country_id="MX", offerings__is_published=True,
    ).distinct().order_by("name_en"))
    for region in regions:
        region.service_cards = list(
            published.filter(region=region).select_related("service", "municipality")
        )
    return render(request, "portal/home.html", {
        "homepage_regions": regions,
        "homepage_us_offerings": published.filter(country_id="US").select_related("service", "region"),
        "homepage_fr_offerings": published.filter(country_id="FR").select_related("service"),
        "contact_services": CatalogService.objects.filter(offerings__is_published=True).distinct().order_by("title_en"),
    })


def wordmark(request):
    return FileResponse(
        open(settings.BASE_DIR / "galiel_wordmark_animation.html", "rb"),
        content_type="text/html; charset=utf-8",
    )


def register(request):
    pending_service = _capture_pending_service(request)
    if request.user.is_authenticated:
        return redirect("service_start" if pending_service else "dashboard")

    if request.method == "POST":
        form = GalielRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save(commit=False)
                    user.is_active = False
                    user.save()
                    profile = user.profile
                    for field in ("phone", "company", "tax_id", "address", "country", "preferred_language"):
                        setattr(profile, field, form.cleaned_data[field].strip())
                    profile.save()
                    send_activation_email(request, user)
            except Exception:
                logger.exception("Galiel account registration or activation email failed")
                form.add_error(None, "We couldn't send your confirmation email. Please try again later.")
            else:
                request.session["registered_email"] = user.email
                return redirect("registration_complete")
    else:
        initial_language = request.GET.get("lang")
        form = GalielRegistrationForm(
            initial={"preferred_language": initial_language}
            if initial_language in {"en", "es", "fr"}
            else None
        )

    label = _pending_service_label(pending_service)
    return render(
        request,
        "portal/register.html",
        {
            "form": form,
            "pending_service": pending_service,
            "pending_service_label": label,
        },
    )


def registration_complete(request):
    email = request.session.pop("registered_email", "")
    code = request.session.get("pending_service", "")
    label = _pending_service_label(code)
    return render(
        request,
        "portal/registration_complete.html",
        {
            "registered_email": email,
            "pending_service": code,
            "pending_service_label": label,
        },
    )


def activate_account(request, uidb64, token):
    """Single-use, time-limited email confirmation."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is None or not default_token_generator.check_token(user, token):
        return render(request, "portal/activation_invalid.html", status=400)
    if not user.is_active:
        user.is_active = True
        user.save(update_fields=["is_active"])
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    messages.success(request, "Your email is confirmed. Welcome to Galiel!")
    return redirect("service_start" if request.session.get("pending_service") else "dashboard")


@require_POST
def resend_activation(request):
    """Throttle repeated requests and avoid account enumeration."""
    from django.utils import timezone
    email = (request.POST.get("email") or "").strip().lower()
    last = request.session.get("activation_resend_at", 0)
    now = int(timezone.now().timestamp())
    if now - last < 120:
        messages.info(request, "Please wait before requesting another link.")
        return redirect("registration_complete")
    request.session["activation_resend_at"] = now
    user = User.objects.filter(email__iexact=email, is_active=False).first()
    if user:
        try:
            send_activation_email(request, user)
        except Exception:
            logger.exception("Galiel activation email resend failed")
            messages.error(request, "Email delivery is unavailable. Please try again later.")
            return redirect("registration_complete")
    messages.info(request, "If this email has an unverified account, a new link has been sent.")
    return redirect("registration_complete")


@never_cache
@login_required
def dashboard(request):
    applications = ServiceApplication.objects.filter(client=request.user).select_related(
        "offering__service", "conversation"
    )
    paid_statuses = ("paid", "under_review", "missing_documents", "submitted", "in_process", "ready")
    return render(request, "portal/dashboard.html", {
        "client_documents": ClientDocument.objects.filter(owner=request.user),
        "case_documents": ApplicationDocument.objects.filter(application__client=request.user, is_invoice=False).select_related("application"),
        "case_invoices": ApplicationDocument.objects.filter(application__client=request.user, is_invoice=True).select_related("application"),
        "document_count": ClientDocument.objects.filter(owner=request.user).count() + ApplicationDocument.objects.filter(application__client=request.user).count(),
        "payment_count": applications.filter(payment_confirmed_at__isnull=False).count(),
        "client_conversations": ClientConversation.objects.filter(client=request.user)[:10],
        "applications": applications,
        "active_count": applications.filter(status__in=paid_statuses).count(),
        "paid_applications": applications.filter(payment_confirmed_at__isnull=False),
        "service_groups": workspace_service_groups(),
    })


@never_cache
@login_required
def profile(request):
    return render(request, "portal/profile.html")


@never_cache
@login_required
def profile_edit(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("profile")
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, "portal/profile_edit.html", {"form": form})


@never_cache
@login_required
def service_start(request):
    code = request.session.get("pending_service", "")
    if not code:
        return redirect("dashboard")

    offering = ServiceOffering.objects.filter(
        service__slug=code, is_published=True,
    ).first()
    if offering:
        request.session.pop("pending_service", None)
        return redirect("service_intake", offering_id=offering.pk)
    label = SERVICE_LABELS.get(code, code.replace("-", " ").title())
    return render(
        request,
        "portal/service_start.html",
        {
            "service_code": code,
            "service_label": label,
        },
    )

@never_cache
@login_required
def document_upload(request):
    if request.method == "POST":
        form = ClientDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.owner = request.user
            document.original_filename = Path(form.cleaned_data["file"].name).name[:255]
            document.save()
            messages.success(request, "Document uploaded successfully.")
            return redirect(reverse("dashboard") + "#documents")
    else:
        form = ClientDocumentForm()
    return render(request, "portal/document_upload.html", {"form": form})


@never_cache
@login_required
def document_download(request, document_id):
    document = get_object_or_404(ClientDocument, pk=document_id, owner=request.user)
    try:
        stream = document.file.open("rb")
    except (OSError, ValueError):
        raise Http404("Document not found")
    return FileResponse(stream, as_attachment=True, filename=document.original_filename)


@never_cache
@login_required
def messages_inbox(request):
    if request.user.is_staff:
        conversations = ClientConversation.objects.select_related("client").all()
    else:
        conversations = ClientConversation.objects.filter(client=request.user)
    service = request.GET.get("service", "")
    subject = f"Inquiry: {SERVICE_LABELS[service]}" if service in SERVICE_LABELS else ""
    offering_id = request.GET.get("offering", "")
    if offering_id.isdecimal():
        offering = ServiceOffering.objects.filter(pk=offering_id, is_published=True).select_related(
            "service", "municipality", "region", "country"
        ).first()
        if offering:
            place = offering.municipality or offering.region or offering.country
            subject = f"Inquiry: {offering.service.title_en} — {place}"[:160]
    return render(request, "portal/messages.html", {
        "conversations": conversations,
        "form": NewConversationForm(initial={"subject": subject}),
    })


@login_required
@require_POST
def conversation_new(request):
    if request.user.is_staff:
        return HttpResponseForbidden("Staff should reply to existing client conversations.")
    form = NewConversationForm(request.POST)
    if not form.is_valid():
        conversations = ClientConversation.objects.filter(client=request.user)
        return render(request, "portal/messages.html", {
            "form": form, "conversations": conversations,
        })
    with transaction.atomic():
        conversation = ClientConversation.objects.create(
            client=request.user, subject=form.cleaned_data["subject"],
        )
        ClientMessage.objects.create(
            conversation=conversation, sender=request.user, body=form.cleaned_data["body"],
        )
    return redirect("conversation_detail", conversation_id=conversation.pk)


@never_cache
@login_required
def conversation_detail(request, conversation_id):
    visible = ClientConversation.objects.select_related("client").prefetch_related("entries__sender")
    if not request.user.is_staff:
        visible = visible.filter(client=request.user)
    conversation = get_object_or_404(visible, pk=conversation_id)
    if request.method == "POST":
        form = ReplyForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                ClientMessage.objects.create(
                    conversation=conversation, sender=request.user,
                    body=form.cleaned_data["body"],
                )
                conversation.save(update_fields=["updated_at"])
            return redirect("conversation_detail", conversation_id=conversation.pk)
    else:
        form = ReplyForm()
    return render(request, "portal/conversation_detail.html", {
        "conversation": conversation, "form": form,
    })


@never_cache
@login_required
def service_catalog(request):
    """Published services only, filtered in country -> region -> municipality order."""
    locale = request.GET.get("lang") or request.COOKIES.get("galiel_lang", "")
    if locale not in ("en", "es", "fr"):
        try:
            locale = request.user.profile.preferred_language
        except Exception:
            locale = "en"
    country_code = request.GET.get("country", "")[:2].upper()
    region_id = request.GET.get("region", "")
    municipality_id = request.GET.get("municipality", "")
    selected_country = country_code if CatalogCountry.objects.filter(pk=country_code).exists() else ""
    regions = CatalogRegion.objects.filter(country_id=selected_country) if selected_country else CatalogRegion.objects.none()
    selected_region = region_id if region_id.isdecimal() and regions.filter(pk=region_id).exists() else ""
    municipalities = CatalogMunicipality.objects.filter(region_id=selected_region) if selected_region else CatalogMunicipality.objects.none()
    selected_municipality = municipality_id if municipality_id.isdecimal() and municipalities.filter(pk=municipality_id).exists() else ""
    offerings = ServiceOffering.objects.filter(is_published=True).select_related(
        "service", "country", "region", "municipality",
    )
    if country_code:
        offerings = offerings.filter(country_id=selected_country) if selected_country else offerings.none()
    if region_id:
        offerings = offerings.filter(region_id=selected_region) if selected_region else offerings.none()
    if municipality_id:
        offerings = offerings.filter(municipality_id=selected_municipality) if selected_municipality else offerings.none()
    return render(request, "portal/service_catalog.html", {
        "locale": locale,
        "countries": CatalogCountry.objects.all(),
        "regions": regions,
        "municipalities": municipalities,
        "selected_country": selected_country,
        "selected_region": str(selected_region),
        "selected_municipality": str(selected_municipality),
        "offerings": list(offerings),
    })


def _catalog_locale(request):
    lang = request.GET.get("lang") or request.COOKIES.get("galiel_lang", "")
    if lang not in ("en", "es", "fr") and request.user.is_authenticated:
        lang = getattr(getattr(request.user, "profile", None), "preferred_language", "en")
    return lang if lang in ("en", "es", "fr") else "en"


def _localized(record, stem, locale):
    return getattr(record, stem + "_" + locale)


def _published_offerings(request):
    """Shared filter semantics for HTML and JSON. Empty filters mean 'all'."""
    qs = ServiceOffering.objects.filter(is_published=True).select_related(
        "country", "region", "municipality", "service",
    )
    country = request.GET.get("country", "").upper()
    region = request.GET.get("region", "")
    municipality = request.GET.get("municipality", "")
    if country:
        qs = qs.filter(country_id=country)
    if region:
        if not region.isdecimal():
            return qs.none()
        qs = qs.filter(region_id=region)
    if municipality:
        if not municipality.isdecimal():
            return qs.none()
        qs = qs.filter(municipality_id=municipality)
    return qs


def catalog_api(request):
    """Read-only JSON for the homepage and authenticated service catalog."""
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    locale = _catalog_locale(request)
    country = request.GET.get("country", "").upper()
    region = request.GET.get("region", "")
    if len(country) > 2 or (region and not region.isdecimal()):
        return JsonResponse({"error": "Invalid location filter"}, status=400)

    regions = CatalogRegion.objects.filter(country_id=country).order_by("name_en") if country else CatalogRegion.objects.none()
    municipalities = CatalogMunicipality.objects.filter(region_id=region).order_by("name_en") if region else CatalogMunicipality.objects.none()
    offerings = []
    for item in _published_offerings(request):
        place = item.municipality or item.region or item.country
        offerings.append({
            "id": item.pk,
            "service": _localized(item.service, "title", locale),
            "code": item.service.slug,
            "country": item.country_id,
            "location": _localized(place, "name", locale),
            "price_type": item.price_type,
            "price": str(item.base_fee) if item.base_fee is not None else (str(item.price) if item.price is not None else None),
            "base_fee": str(item.base_fee) if item.base_fee is not None else None,
            "included_m2": str(item.included_m2) if item.included_m2 is not None else None,
            "per_extra_m2": str(item.per_extra_m2) if item.per_extra_m2 is not None else None,
            "fee_covers": fee_note(item, locale),
            "currency": item.currency,
            "estimated_min_business_days": item.estimated_min_business_days,
            "estimated_max_business_days": item.estimated_max_business_days,
            "start_url": reverse("service_intake", args=[item.pk]),
        })
    return JsonResponse({
        "regions": [{"id": r.pk, "name": _localized(r, "name", locale)} for r in regions],
        "municipalities": [{"id": m.pk, "name": _localized(m, "name", locale)} for m in municipalities],
        "offerings": offerings,
    })


@never_cache
@login_required
def service_intake(request, offering_id):
    """Service step one: describe the offering and explicitly start a draft."""
    offering = get_object_or_404(
        ServiceOffering.objects.select_related("country", "region", "municipality", "service"),
        pk=offering_id, is_published=True,
    )
    return render(request, "portal/service_intake.html", {
        "offering": offering, "locale": _catalog_locale(request),
    })



def galiel_signature_png(request):
    """Email-compatible PNG served from the exact canonical homepage signature."""
    import base64
    from django.conf import settings
    from django.http import HttpResponse
    from django.views.decorators.cache import cache_control
    from pathlib import Path
    svg = (Path(settings.BASE_DIR) / "portal" / "static" / "portal" / "galiel-signature.svg").read_text(encoding="utf-8")
    png = base64.b64decode(svg.split("base64,", 1)[1].split('"', 1)[0])
    response = HttpResponse(png, content_type="image/png")
    response["Cache-Control"] = "public, max-age=604800"
    response["X-Content-Type-Options"] = "nosniff"
    return response
