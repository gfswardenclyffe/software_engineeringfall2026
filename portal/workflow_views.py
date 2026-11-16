"""Resumable service applications and payment-confirmed case workflow.

Client payment success is trusted ONLY after a verified Stripe webhook; the
success redirect never marks an application paid.
"""
import logging
import os
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from pathlib import Path

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.http import FileResponse, Http404, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import (
    ServiceOffering, ServiceApplication, ServiceRequirement, ApplicationDocument,
    ApplicationEvent, ClientConversation, ClientMessage,
)

logger = logging.getLogger(__name__)
MAX_FILE_BYTES = 10 * 1024 * 1024
CENT = Decimal("0.01")
PAYMENT_STATUSES = {"paid", "under_review", "missing_documents", "submitted", "in_process", "ready"}


def _language(request):
    lang = request.GET.get("lang") or getattr(getattr(request.user, "profile", None), "preferred_language", "en")
    return lang if lang in ("en", "es", "fr") else "en"


def _display_title(offering, lang):
    return getattr(offering.service, "title_" + lang)


def _display_place(offering, lang):
    place = offering.municipality or offering.region or offering.country
    return getattr(place, "name_" + lang)


def _application(request, application_id):
    return get_object_or_404(
        ServiceApplication.objects.select_related("client", "offering__service", "offering__country",
            "offering__region", "offering__municipality", "conversation"),
        pk=application_id, client=request.user,
    )


def _requirements(app, kind):
    return app.offering.requirements.filter(kind=kind).order_by("display_order", "id")


def _form_for(app, request):
    class AnswerForm(forms.Form):
        pass
    form = AnswerForm(request.POST if request.method == 'POST' else None)
    for req in _requirements(app, "question"):
        lang = _language(request)
        form.fields["answer_" + str(req.pk)] = forms.CharField(
            max_length=1000, required=req.is_required,
            label=getattr(req, "label_" + lang),
            initial=app.answers.get(str(req.pk), ""),
            widget=forms.TextInput(attrs={"autocomplete": "off"}),
        )
    return form


def _price_for(app):
    """Compute payable amount from server-side config only, never browser prices."""
    offer = app.offering
    if app.quoted_amount is not None and app.status in ("quoted", "awaiting_payment"):
        return app.quoted_amount.quantize(CENT), Decimal("0.00"), app.quoted_amount.quantize(CENT)
    if offer.price_type == "quote" or offer.price is None:
        return None, None, None
    if offer.price_type == "starting":
        if offer.deposit_amount is None or offer.deposit_amount <= 0:
            return None, None, None
        base = offer.deposit_amount
    else:
        base = offer.price
    base = base.quantize(CENT)
    tax = (base * offer.tax_rate / 100).quantize(CENT, rounding=ROUND_HALF_UP)
    return base, tax, base + tax


def _ensure_conversation(app):
    if app.conversation_id:
        return app.conversation
    conversation = ClientConversation.objects.create(
        client=app.client, subject=f"{app.number}: {app.service_title}"[:160],
    )
    app.conversation = conversation
    app.save(update_fields=["conversation", "updated_at"])
    return conversation


def _set_status(app, status, note=""):
    if app.status != status:
        app.status = status
        app.save(update_fields=["status", "updated_at"])
        ApplicationEvent.objects.create(application=app, status=status, note=note[:400])


def _full_name(user):
    return user.get_full_name().strip() or user.email


def _notify_client(app, subject, summary):
    if not app.client.email:
        return
    track = "https://galiel.wardenclyffefirm.com" + reverse("application_track", args=[app.pk])
    body = (
        f"Galiel by Wardenclyffe\n\nHello {_full_name(app.client)},\n\n"
        f"{summary}\n\nService: {app.service_title}\n"
        f"Reference: {app.number}\n"
        f"Estimated delivery: {app.estimated_delivery or 'To be confirmed'}\n"
        f"Track your process: {track}\n\n"
        "Wardenclyffe Inc. is a private service provider; approval and agency timelines are not guaranteed.\n"
    )
    if app.payment_confirmed_at:
        body += "\nPayment record: https://galiel.wardenclyffefirm.com" + reverse("application_receipt", args=[app.pk]) + "\n"
    if app.stripe_receipt_url:
        body += f"\nCard processor receipt: {app.stripe_receipt_url}\n"
    if app.payment_confirmed_at:
        body += "\nA tax invoice, where applicable, will be issued separately.\n"
    msg = EmailMultiAlternatives(
        f"Galiel · {subject} · {app.number}", body,
        settings.DEFAULT_FROM_EMAIL, [app.client.email],
    )
    html = (
        '<div style="background:#f6f1ea;padding:32px;font:15px Arial,sans-serif;color:#211c19">'
        '<div style="max-width:600px;margin:auto;background:#fffdf9;border:1px solid #e9dbcf;padding:30px">'
        '<h1 style="font:italic 32px Georgia,serif;margin:0">Galiel'
        '<small style="font:13px Arial,sans-serif"> by Wardenclyffe</small></h1>'
        '<p style="font-size:20px;margin-top:28px">' + escape(subject) + '</p>'
        '<p>Hello ' + escape(_full_name(app.client)) + ',</p>'
        '<p>' + escape(summary) + '</p>'
        '<p><strong>' + escape(app.number) + '</strong> · ' + escape(app.service_title) + '</p>'
        '<p>Estimated delivery: ' + escape(str(app.estimated_delivery or "To be confirmed")) + '</p>'
        '<a style="display:inline-block;border-radius:24px;background:#e96c3c;color:#211c19;padding:13px 20px;text-decoration:none;font-weight:bold" href="' + escape(track) + '">Track my process</a>'
        + (('<p><a href="https://galiel.wardenclyffefirm.com' + reverse("application_receipt", args=[app.pk]) + '">View your Galiel payment record</a></p>') if app.payment_confirmed_at else '')
        + (('<p><a href="' + escape(app.stripe_receipt_url) + '">View Stripe card receipt</a></p>') if app.stripe_receipt_url else '')
        + '<p style="font-size:12px;color:#786c62;margin-top:26px">Government processing and agency approval are not guaranteed. Tax invoices are issued separately when applicable.</p>'
        '</div></div>'
    )
    msg.attach_alternative(html, "text/html")
    msg.send(fail_silently=False)


@never_cache
@login_required
def application_start(request, offering_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    offer = get_object_or_404(
        ServiceOffering.objects.select_related("service", "country", "region", "municipality"),
        pk=offering_id, is_published=True,
    )
    if request.user.is_staff:
        return HttpResponseForbidden("Staff cannot create client checkout applications.")
    with transaction.atomic():
        app = ServiceApplication.objects.create(
            client=request.user, offering=offer,
            service_title=offer.service.title_en,
            location_label=str(offer.municipality or offer.region or offer.country),
            currency=offer.currency,
        )
        ApplicationEvent.objects.create(application=app, status="draft", note="Application created")
    return redirect("application_step", application_id=app.pk, step=1)


@never_cache
@login_required
def application_step(request, application_id, step):
    app = _application(request, application_id)
    if step not in (1, 2, 3, 4, 5, 6):
        raise Http404
    lang = _language(request)
    offer = app.offering
    paid = app.status in PAYMENT_STATUSES
    if paid and step != 6:
        return redirect("application_track", application_id=app.pk)
    if step == 6 and not paid:
        return redirect("application_step", application_id=app.pk, step=5)
    if step > app.step and step != 6:
        return redirect("application_step", application_id=app.pk, step=app.step)
    if request.method == "POST":
        if step == 1:
            app.step = max(app.step, 2)
            app.save(update_fields=["step", "updated_at"])
            return redirect("application_step", application_id=app.pk, step=2)
        if step == 2:
            form = _form_for(app, request)
            if form.is_valid():
                app.answers = {key[7:]: val for key, val in form.cleaned_data.items()}
                app.step = max(app.step, 3)
                app.save(update_fields=["answers", "step", "updated_at"])
                return redirect("application_step", application_id=app.pk, step=3)
        if step == 3:
            app.notes = request.POST.get("notes", "")[:5000]
            app.step = max(app.step, 4)
            app.save(update_fields=["notes", "step", "updated_at"])
            return redirect("application_step", application_id=app.pk, step=4)
        if step == 4:
            if request.POST.get("terms") != "yes":
                messages.error(request, "You must accept the terms before continuing.")
            elif any(str(req.pk) not in app.answers for req in _requirements(app, "question") if req.is_required):
                messages.error(request, "Complete the required information before continuing.")
            elif any(not app.documents.filter(requirement=req).exists() for req in _requirements(app, "document") if req.is_required):
                messages.error(request, "Upload every required document before continuing.")
            else:
                base, tax, total = _price_for(app)
                app.subtotal, app.tax_amount, app.total = base, tax, total
                app.currency = offer.currency
                app.terms_accepted_at = timezone.now()
                app.step = max(app.step, 5)
                app.save(update_fields=["subtotal", "tax_amount", "total", "currency", "terms_accepted_at", "step", "updated_at"])
                return redirect("application_step", application_id=app.pk, step=5)
        if step == 5 and request.POST.get("action") == "quote" and app.total is None and app.terms_accepted_at:
            _set_status(app, "quote_requested", "Client requested a quote")
            _ensure_conversation(app)
            messages.success(request, "Your quotation request has been saved. You can track it in My processes.")
            return redirect("application_track", application_id=app.pk)
    form = _form_for(app, request) if step == 2 else None
    base, tax, total = _price_for(app)
    uploaded = {doc.requirement_id: doc for doc in app.documents.filter(requirement__isnull=False)}
    requirements = [(req, uploaded.get(req.pk)) for req in _requirements(app, "document")]
    questions = [(req, app.answers.get(str(req.pk), "")) for req in _requirements(app, "question")]
    return render(request, "portal/application_step.html", {
        "application": app, "offering": offer, "step": step, "locale": lang,
        "service_name": _display_title(offer, lang),
        "place_name": _display_place(offer, lang), "form": form,
        "requirements": requirements, "questions": questions,
        "base": base, "tax": tax, "total": total,
        "checkout_cancelled": request.GET.get("canceled") == "1",
        "is_quote": total is None, "stripe_configured": bool(
            os.getenv("GALIEL_STRIPE_SECRET_KEY") and os.getenv("GALIEL_STRIPE_WEBHOOK_SECRET")
        ),
    })


@login_required
@require_POST
def application_autosave(request, application_id):
    app = _application(request, application_id)
    if app.status != "draft":
        return JsonResponse({"error": "Application is no longer a draft."}, status=409)
    payload = {}
    allowed = {str(req.pk) for req in _requirements(app, "question")}
    for key, value in request.POST.items():
        if key.startswith("answer_") and key[7:] in allowed:
            payload[key[7:]] = value[:1000]
    app.answers = {**app.answers, **payload}
    if "notes" in request.POST:
        app.notes = request.POST["notes"][:5000]
    app.save(update_fields=["answers", "notes", "updated_at"])
    return JsonResponse({"saved": True})


def _verify_file(file):
    if file.size > MAX_FILE_BYTES or file.size < 4:
        raise forms.ValidationError("File must be at most 10 MB and not empty.")
    extension = Path(file.name).suffix.lower()
    head = file.read(12)
    file.seek(0)
    if extension == ".pdf" and head.startswith(b"%PDF-"):
        return "application/pdf"
    if extension == ".png" and head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if extension in (".jpg", ".jpeg") and head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    raise forms.ValidationError("Only valid PDF, JPG and PNG files are accepted.")


@login_required
@require_POST
def application_upload(request, application_id, requirement_id):
    app = _application(request, application_id)
    if app.status not in ("draft", "missing_documents"):
        return HttpResponseForbidden("Files can be changed only in a draft or when documents are requested.")
    req = get_object_or_404(ServiceRequirement, pk=requirement_id, offering=app.offering, kind="document")
    file = request.FILES.get("file")
    if not file:
        messages.error(request, "Select a PDF, JPG or PNG file.")
    else:
        try:
            file_type = _verify_file(file)
        except forms.ValidationError as exc:
            messages.error(request, str(exc.message))
        else:
            previous = list(app.documents.filter(requirement=req))
            doc = ApplicationDocument.objects.create(
                application=app, requirement=req,
                file=file, original_filename=Path(file.name).name[:255],
                content_type=file_type, size=file.size,
            )
            for old in previous:
                old.file.delete(save=False)
                old.delete()
            messages.success(request, f"Uploaded {doc.original_filename}")
    return redirect("application_track", application_id=app.pk) if app.status == "missing_documents" else redirect("application_step", application_id=app.pk, step=3)


@login_required
@require_POST
def application_delete_file(request, application_id, document_id):
    app = _application(request, application_id)
    if app.status not in ("draft", "missing_documents"):
        return HttpResponseForbidden()
    doc = get_object_or_404(ApplicationDocument, application=app, pk=document_id, is_deliverable=False)
    doc.file.delete(save=False)
    doc.delete()
    return redirect("application_track", application_id=app.pk) if app.status == "missing_documents" else redirect("application_step", application_id=app.pk, step=3)


@never_cache
@login_required
def application_download(request, application_id, document_id):
    app = _application(request, application_id)
    doc = get_object_or_404(ApplicationDocument, application=app, pk=document_id)
    try:
        stream = doc.file.open("rb")
    except (ValueError, OSError):
        raise Http404
    response = FileResponse(stream, as_attachment=False, filename=doc.original_filename)
    response["X-Content-Type-Options"] = "nosniff"
    response["Content-Security-Policy"] = "sandbox"
    return response


@never_cache
@login_required
def application_track(request, application_id):
    app = _application(request, application_id)
    requirements = [(req, app.documents.filter(requirement=req).first())
                    for req in _requirements(app, "document")]
    return render(request, "portal/application_track.html", {
        "application": app, "events": app.events.all(), "requirements": requirements,
    })


@never_cache
@login_required
def application_receipt(request, application_id):
    app = _application(request, application_id)
    if not app.payment_confirmed_at:
        raise Http404("No verified payment exists for this application.")
    return render(request, "portal/application_receipt.html", {"application": app})


@login_required
@require_POST
def application_checkout(request, application_id):
    app = _application(request, application_id)
    if app.status in PAYMENT_STATUSES:
        return redirect("application_track", application_id=app.pk)
    if app.status not in ("draft", "quoted", "awaiting_payment") or not app.terms_accepted_at:
        return HttpResponseForbidden("Review and accept terms before payment.")
    if app.step < 5:
        return HttpResponseForbidden("Complete the application before payment.")
    if not (os.getenv("GALIEL_STRIPE_SECRET_KEY") and os.getenv("GALIEL_STRIPE_WEBHOOK_SECRET")):
        messages.error(request, "Secure checkout is not configured yet. No payment was taken.")
        return redirect("application_step", application_id=app.pk, step=5)
    base, tax, total = _price_for(app)
    # When a quote was approved, use the exact approved amount; otherwise recheck snapshot.
    if total is None or total <= 0 or app.currency not in ("MXN", "USD", "EUR"):
        messages.error(request, "The service needs a confirmed price before checkout.")
        return redirect("application_step", application_id=app.pk, step=5)
    if app.status == "draft" and app.total != total:
        messages.error(request, "Pricing changed. Please review the updated total before paying.")
        return redirect("application_step", application_id=app.pk, step=4)
    try:
        import stripe
        stripe.api_key = os.environ["GALIEL_STRIPE_SECRET_KEY"]
        if app.stripe_checkout_session:
            old = stripe.checkout.Session.retrieve(app.stripe_checkout_session)
            if old.get("status") == "complete":
                messages.info(request, "Your payment is being verified. Please check your process before paying again.")
                return redirect("application_track", application_id=app.pk)
            if old.get("status") == "open":
                if (old.get("amount_total") == int(total * 100)
                        and (old.get("currency") or "").lower() == app.currency.lower()):
                    return redirect(str(old.url))
                stripe.checkout.Session.expire(app.stripe_checkout_session)
        stripe_session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            customer_email=app.client.email,
            client_reference_id=str(app.pk),
            metadata={"application_id": str(app.pk)},
            line_items=[{"price_data": {
                "currency": app.currency.lower(), "unit_amount": int(total * 100),
                "product_data": {"name": app.service_title[:180]},
            }, "quantity": 1}],
            success_url=request.build_absolute_uri(reverse("application_step", args=[app.pk, 6])) + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=request.build_absolute_uri(reverse("application_step", args=[app.pk, 5])) + "?canceled=1",
        )
    except Exception:
        logger.exception("Stripe Checkout session creation failed for application %s", app.pk)
        messages.error(request, "Secure payment could not be started. Please try again later.")
        return redirect("application_step", application_id=app.pk, step=5)
    app.stripe_checkout_session = stripe_session.id
    app.subtotal, app.tax_amount, app.total = base, tax, total
    app.currency = app.offering.currency
    app.save(update_fields=["stripe_checkout_session", "subtotal", "tax_amount", "total", "currency", "updated_at"])
    return redirect(stripe_session.url)


def _estimated_delivery(max_business_days):
    """Provisional business-day estimate, excluding weekends (not holidays)."""
    if max_business_days is None:
        return None
    day = timezone.localdate()
    remaining = max_business_days
    while remaining > 0:
        day += timedelta(days=1)
        if day.weekday() < 5:
            remaining -= 1
    return day


def _confirm_paid(app, session):
    """Idempotently activate the case after a verified, paid Checkout Session."""
    receipt = ""
    if os.getenv("GALIEL_STRIPE_SECRET_KEY") and session.get("payment_intent"):
        try:
            import stripe
            stripe.api_key = os.environ["GALIEL_STRIPE_SECRET_KEY"]
            intent = stripe.PaymentIntent.retrieve(session["payment_intent"], expand=["latest_charge"])
            charge = intent.get("latest_charge")
            if charge and hasattr(charge, "get"):
                receipt = charge.get("receipt_url") or ""
        except Exception:
            logger.exception("Unable to retrieve receipt link for application %s", app.pk)
    with transaction.atomic():
        app = ServiceApplication.objects.select_for_update().select_related("client", "offering").get(pk=app.pk)
        if app.status in PAYMENT_STATUSES:
            return
        if session.get("payment_status") != "paid":
            return
        if app.stripe_checkout_session != session.get("id"):
            raise ValueError("Checkout session does not match application")
        if str(app.pk) != str(session.get("client_reference_id")):
            raise ValueError("Checkout client reference mismatch")
        if app.total is None or int(app.total * 100) != session.get("amount_total"):
            raise ValueError("Checkout amount mismatch")
        if app.currency.lower() != session.get("currency", "").lower():
            raise ValueError("Checkout currency mismatch")
        app.payment_confirmed_at = timezone.now()
        app.stripe_payment_intent = session.get("payment_intent") or ""
        app.stripe_receipt_url = receipt[:1000]
        app.estimated_delivery = _estimated_delivery(app.offering.estimated_max_business_days)
        app.save(update_fields=["payment_confirmed_at", "stripe_payment_intent", "stripe_receipt_url", "estimated_delivery", "updated_at"])
        _set_status(app, "paid", "Stripe payment confirmed")
        conversation = _ensure_conversation(app)
        ClientMessage.objects.create(
            conversation=conversation, sender=app.client,
            body=f"Application {app.number} paid and submitted for review.",
        )
        def notify():
            try:
                _notify_client(app, "Payment confirmed", f"Payment received: {app.currency} {app.total}. Your application is now being processed. Your payment receipt is available from your payment provider.")
                ServiceApplication.objects.filter(pk=app.pk, confirmation_sent_at__isnull=True).update(confirmation_sent_at=timezone.now())
            except Exception:
                logger.exception("Could not email payment confirmation for application %s", app.pk)
        transaction.on_commit(notify)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    secret = os.getenv("GALIEL_STRIPE_WEBHOOK_SECRET")
    if not secret:
        return HttpResponseForbidden("Webhook not configured")
    if len(request.body) > 1024 * 1024:
        return HttpResponseBadRequest("Payload too large")
    try:
        import stripe
        event = stripe.Webhook.construct_event(request.body, request.META.get("HTTP_STRIPE_SIGNATURE", ""), secret)
    except Exception:
        logger.warning("Stripe webhook signature or payload rejected")
        return HttpResponseBadRequest("Invalid Stripe webhook")
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        app_id = session.get("metadata", {}).get("application_id")
        if app_id and str(app_id).isdecimal():
            app = ServiceApplication.objects.filter(pk=app_id).first()
            if app:
                try:
                    _confirm_paid(app, session)
                except (ValueError, InvalidOperation):
                    logger.warning("Rejected mismatched Stripe payment for application %s", app_id)
                    return HttpResponseBadRequest("Payment mismatch")
    return JsonResponse({"received": True})
