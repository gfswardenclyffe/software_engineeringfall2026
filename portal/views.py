from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import FileResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.conf import settings

from .forms import EmailAuthenticationForm, GalielRegistrationForm, UserProfileForm


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
    if service:
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
            user = form.save()
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


@login_required
def dashboard(request):
    return render(request, "portal/dashboard.html")


@login_required
def profile_edit(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("dashboard")
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, "portal/profile_edit.html", {"form": form})


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
