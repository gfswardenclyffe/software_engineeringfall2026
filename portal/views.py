from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from django.http import FileResponse, Http404, HttpResponseForbidden
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
from .models import ClientDocument, ClientConversation, ClientMessage
from .document_forms import ClientDocumentForm
from .message_forms import NewConversationForm, ReplyForm
from pathlib import Path


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


def _capture_pending_service(request):
    service = (request.GET.get("service") or request.POST.get("service") or "").strip()
    if service in SERVICE_LABELS:
        request.session["pending_service"] = service
    return request.session.get("pending_service", "")


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
        context["pending_service_label"] = SERVICE_LABELS.get(
            code, code.replace("-", " ").title() if code else ""
        )
        return context

    def get_success_url(self):
        code = self.request.session.get("pending_service", "")
        if code:
            return reverse("service_start")
        return reverse("dashboard")


def home(request):
    return render(request, "portal/home.html")


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

    label = SERVICE_LABELS.get(
        pending_service, pending_service.replace("-", " ").title() if pending_service else ""
    )
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
    label = SERVICE_LABELS.get(code, code.replace("-", " ").title() if code else "")
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
            messages.error(request, "Email delivery is unavailable. Please try again later.")
            return redirect("registration_complete")
    messages.info(request, "If this email has an unverified account, a new link has been sent.")
    return redirect("registration_complete")


@never_cache
@login_required
def dashboard(request):
    return render(request, "portal/dashboard.html", {
        "client_documents": ClientDocument.objects.filter(owner=request.user),
        "client_conversations": ClientConversation.objects.filter(client=request.user)[:10],
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
    return render(request, "portal/messages.html", {
        "conversations": conversations,
        "form": NewConversationForm(),
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
