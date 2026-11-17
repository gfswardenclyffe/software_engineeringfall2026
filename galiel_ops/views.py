"""New Galiel operational endpoints. Every client-object lookup is owner-filtered."""
from datetime import timedelta
from pathlib import Path
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.core.exceptions import ValidationError
from django import forms
from portal.models import ApplicationDocument, ServiceApplication, ServiceOffering
from .models import Announcement, Reminder, AccountDeletionRequest, FiscalProfile, InvoiceRequest

CATEGORIES = {x[0] for x in Announcement.CATEGORIES}
LOCALES = ("en", "es", "fr")

def locale_for(request):
    value = request.GET.get("lang") or request.COOKIES.get("galiel_lang")
    if not value:
        try:
            value = request.user.profile.preferred_language
        except (AttributeError, Exception):
            value = "en"
    return value if value in LOCALES else "en"

def _active_announcements():
    now = timezone.now()
    return Announcement.objects.filter(published_at__lte=now).filter(
        models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now)
    )

from django.db import models

@login_required
@require_GET
def announcement_list(request):
    category = request.GET.get("category", "")
    items = _active_announcements().select_related("author")
    if category in CATEGORIES:
        items = items.filter(category=category)
    return render(request, "galiel_ops/announcements.html", {
        "items": items[:100], "category": category, "categories": Announcement.CATEGORIES,
        "lang": locale_for(request),
    })

@login_required
@require_GET
def reminder_list(request):
    reminders = Reminder.objects.filter(user=request.user, dismissed=False).select_related("application")
    return render(request, "galiel_ops/reminders.html", {
        "items": reminders[:200], "unread_count": reminders.filter(read_at__isnull=True).count(),
        "lang": locale_for(request)
    })

@login_required
@require_POST
def reminder_read(request, reminder_id):
    reminder = get_object_or_404(Reminder,pk=reminder_id,user=request.user)
    if reminder.read_at is None:
        reminder.read_at=timezone.now()
        reminder.save(update_fields=["read_at"])
    return redirect("galiel_reminders")

@login_required
@require_POST
def reminder_dismiss(request, reminder_id):
    reminder=get_object_or_404(Reminder,pk=reminder_id,user=request.user)
    reminder.dismissed=True
    reminder.save(update_fields=["dismissed"])
    return redirect("galiel_reminders")

@login_required
@require_GET
def unread_count(request):
    return JsonResponse({"unread":Reminder.objects.filter(user=request.user,dismissed=False,read_at__isnull=True).count()})

@login_required
def delete_draft(request, application_id):
    app=get_object_or_404(ServiceApplication,pk=application_id,client=request.user)
    if app.status!="draft" or app.payment_confirmed_at or app.stripe_checkout_session:
        return HttpResponseForbidden("Only draft applications can be deleted.")
    if request.method=="GET":
        return render(request,"galiel_ops/confirm_delete.html",{"application":app,"lang":locale_for(request)})
    if request.method!="POST":
        return HttpResponseForbidden()
    if request.POST.get("confirm") != app.number:
        return HttpResponseForbidden("Type the exact application reference to confirm.")
    paths = [d.file.name for d in app.documents.all() if d.file]
    storage = ApplicationDocument._meta.get_field("file").storage
    with transaction.atomic():
        app.delete()
        def cleanup():
            for name in paths:
                try:
                    storage.delete(name)
                except OSError:
                    # Leftover private bytes are preferable to silently corrupting DB state.
                    import logging
                    logging.getLogger(__name__).exception("Private orphan file cleanup: %s",name)
        transaction.on_commit(cleanup)
    return redirect(reverse("dashboard")+"#processes")

@login_required
@require_POST
def delete_draft_file(request, application_id, document_id):
    app=get_object_or_404(ServiceApplication,pk=application_id,client=request.user,status="draft",payment_confirmed_at__isnull=True,stripe_checkout_session="")
    doc=get_object_or_404(ApplicationDocument,pk=document_id,application=app,is_deliverable=False)
    name=doc.file.name
    storage=doc.file.storage
    with transaction.atomic():
        doc.delete()
        transaction.on_commit(lambda: storage.delete(name) if name else None)
    return redirect("application_step",application_id=app.pk,step=3)

@login_required
@require_POST
def request_account_deletion(request):
    if not AccountDeletionRequest.objects.filter(user=request.user,status__in=["pending","in_review"]).exists():
        AccountDeletionRequest.objects.create(user=request.user)
    return redirect("profile")

class FiscalForm(forms.ModelForm):
    class Meta:
        model=FiscalProfile
        fields=("rfc","razon_social","regimen_fiscal","uso_cfdi","invoice_email")
    def clean_rfc(self):
        value=(self.cleaned_data.get("rfc") or "").strip().upper()
        if value and (len(value) not in (12,13) or not value.isalnum()):
            raise ValidationError("Use a valid-length RFC (12 or 13 alphanumeric characters).")
        return value

@login_required
def fiscal_profile(request):
    instance=FiscalProfile.objects.filter(user=request.user).first()
    if request.method=="POST":
        form=FiscalForm(request.POST,instance=instance)
        if form.is_valid():
            entry=form.save(commit=False)
            entry.user=request.user
            entry.save()
            return redirect("galiel_fiscal_profile")
    else:
        form=FiscalForm(instance=instance)
    return render(request,"galiel_ops/fiscal_profile.html",{"form":form,"lang":locale_for(request)})

@login_required
@require_POST
def request_invoice(request, application_id):
    application=get_object_or_404(ServiceApplication,pk=application_id,client=request.user)
    if request.POST.get("invoice_requested")!="yes":
        return HttpResponseForbidden("Explicit invoice request is required.")
    from django.core.mail import send_mail
    from django.conf import settings
    with transaction.atomic():
        invoice,created=InvoiceRequest.objects.get_or_create(
            application=application,defaults={"user":request.user}
        )
        if created:
            def notify_staff():
                from django.contrib.auth.models import User
                recipients=list(User.objects.filter(is_staff=True,is_active=True)
                                .exclude(email="").values_list("email",flat=True).distinct())
                if recipients:
                    send_mail("Galiel · Manual invoice requested",
                        f"Invoice requested for {application.number}. Review privately in Galiel admin.",
                        settings.DEFAULT_FROM_EMAIL, recipients,fail_silently=False)
                    InvoiceRequest.objects.filter(pk=invoice.pk,staff_notified_at__isnull=True).update(staff_notified_at=timezone.now())
            transaction.on_commit(notify_staff)
    return redirect("application_track",application_id=application.pk)

@require_GET
def help_choices(request):
    lang=locale_for(request)
    return JsonResponse({"lang":lang,"options":["services","documents","processes","person"]})

@require_GET
def help_requirements(request,offering_id):
    offering=get_object_or_404(ServiceOffering.objects.select_related("service"),pk=offering_id,is_published=True)
    lang=locale_for(request)
    fields=list(offering.requirements.filter(kind="document").order_by("display_order","pk").values("label_en","label_es","label_fr","is_required"))
    return JsonResponse({"service":getattr(offering.service,"title_"+lang),
                         "requirements":[{"label":x["label_"+lang],"required":x["is_required"]} for x in fields]})

@login_required
@require_GET
def help_my_processes(request):
    apps=ServiceApplication.objects.filter(client=request.user).order_by("-updated_at")
    return JsonResponse({"processes":[{"reference":a.number,"status":a.get_status_display(),
             "url":reverse("application_track",args=[a.pk])} for a in apps[:20]]})

@require_GET
def help_services(request):
    lang=locale_for(request)
    rows=ServiceOffering.objects.filter(is_published=True).select_related("service").order_by("service__title_en")[:250]
    return JsonResponse({"services":[{"id":entry.pk,
       "title":getattr(entry.service,"title_"+lang)} for entry in rows]})
