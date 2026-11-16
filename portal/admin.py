from django.contrib import admin
from django import forms
from django.db import transaction
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.html import format_html
import logging

logger = logging.getLogger(__name__)
from .workflow_views import _notify_client, _verify_file

from .models import Profile, ClientConversation, ClientMessage, CatalogCountry, CatalogRegion, CatalogMunicipality, CatalogService, ServiceOffering, ServiceRequirement, ServiceApplication, ApplicationDocument, ApplicationEvent, ContactLead


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "company", "country", "preferred_language")
    search_fields = (
        "user__username",
        "user__email",
        "company",
        "tax_id",
        "phone",
        "country",
    )


class ClientMessageInline(admin.TabularInline):
    model = ClientMessage
    extra = 0
    readonly_fields = ("sender", "body", "created_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ClientConversation)
class ClientConversationAdmin(admin.ModelAdmin):
    list_display = ("subject", "client", "created_at", "updated_at")
    search_fields = ("subject", "client__email", "client__username")
    readonly_fields = ("created_at", "updated_at")
    inlines = [ClientMessageInline]


@admin.register(ClientMessage)
class ClientMessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "sender", "created_at")
    search_fields = ("conversation__subject", "sender__email", "body")
    readonly_fields = ("conversation", "sender", "body", "created_at")

    def has_add_permission(self, request):
        return False


@admin.register(CatalogCountry)
class CatalogCountryAdmin(admin.ModelAdmin):
    list_display = ("code", "name_en", "name_es", "name_fr")
    search_fields = ("code", "name_en", "name_es", "name_fr")


@admin.register(CatalogRegion)
class CatalogRegionAdmin(admin.ModelAdmin):
    list_display = ("name_en", "country", "slug")
    list_filter = ("country",)
    search_fields = ("name_en", "name_es", "name_fr")
    prepopulated_fields = {"slug": ("name_en",)}


@admin.register(CatalogMunicipality)
class CatalogMunicipalityAdmin(admin.ModelAdmin):
    list_display = ("name_en", "region", "slug")
    list_filter = ("region__country",)
    search_fields = ("name_en", "name_es", "name_fr", "region__name_en")
    prepopulated_fields = {"slug": ("name_en",)}


@admin.register(CatalogService)
class CatalogServiceAdmin(admin.ModelAdmin):
    list_display = ("title_en", "slug")
    search_fields = ("title_en", "title_es", "title_fr", "slug")
    prepopulated_fields = {"slug": ("title_en",)}


class ServiceRequirementInline(admin.TabularInline):
    model = ServiceRequirement
    extra = 0
    fields = ("display_order", "kind", "label_en", "label_es", "label_fr", "is_required")


@admin.register(ServiceOffering)
class ServiceOfferingAdmin(admin.ModelAdmin):
    list_display = ("service", "country", "region", "municipality", "price_type", "price", "currency", "is_published")
    list_filter = ("is_published", "country", "price_type", "currency")
    search_fields = ("service__title_en", "municipality__name_en", "region__name_en")
    list_select_related = ("service", "country", "region", "municipality")
    inlines = [ServiceRequirementInline]
    fieldsets = (
        ("Service & location", {"fields": ("service", "country", "region", "municipality")}),
        ("Commercial details", {"fields": ("price_type", "price", "deposit_amount", "tax_rate", "currency", "estimated_min_business_days", "estimated_max_business_days")}),
        ("Visibility & internal notes", {"fields": ("is_published", "manager_notes")}),
    )


class ApplicationAdminForm(forms.ModelForm):
    class Meta:
        model = ServiceApplication
        fields = "__all__"

    def clean(self):
        values = super().clean()
        new_status = values.get("status")
        old = ServiceApplication.objects.filter(pk=self.instance.pk).first() if self.instance.pk else None
        if old:
            if new_status == "paid" and old.status != "paid":
                raise ValidationError("Only a verified payment webhook can mark a case Paid.")
            if new_status in ("under_review", "missing_documents", "submitted", "in_process", "ready") and not old.payment_confirmed_at:
                raise ValidationError("A payment-confirmed case is required for this processing status.")
            if new_status == "quoted":
                amount = values.get("quoted_amount")
                if old.status not in ("quote_requested", "quoted", "awaiting_payment") or amount is None or amount <= 0:
                    raise ValidationError("A positive staff-approved quote is required for a quote-requested application.")
            if (old.payment_confirmed_at or old.stripe_checkout_session) and values.get("quoted_amount") != old.quoted_amount:
                raise ValidationError("Cannot change a quotation after Stripe Checkout has started. Resolve or expire the session first.")
            if old.payment_confirmed_at and new_status not in ("paid", "under_review", "missing_documents", "submitted", "in_process", "ready"):
                raise ValidationError("A paid case cannot be returned to an unpaid status.")
        return values


class ApplicationDocumentAdminForm(forms.ModelForm):
    class Meta:
        model = ApplicationDocument
        fields = "__all__"

    def clean_file(self):
        file = self.cleaned_data.get("file")
        if file and hasattr(file, "size"):
            _verify_file(file)
        return file

    def save(self, commit=True):
        obj = super().save(commit=False)
        file = self.cleaned_data.get("file")
        if file and hasattr(file, "size"):
            obj.original_filename = file.name.rsplit("/", 1)[-1][:255]
            obj.content_type = _verify_file(file)
            obj.size = file.size
        if commit:
            obj.save()
            self.save_m2m()
        return obj


class ApplicationDocumentInline(admin.TabularInline):
    model = ApplicationDocument
    form = ApplicationDocumentAdminForm
    extra = 0
    fields = ("requirement", "file", "staff_preview", "original_filename", "review_status", "staff_note", "is_deliverable", "is_invoice")
    readonly_fields = ("staff_preview", "original_filename")

    @admin.display(description="Private file")
    def staff_preview(self, obj):
        if obj and obj.pk:
            return format_html('<a href="{}" target="_blank" rel="noopener">Preview file</a>',
                reverse("staff_document_download", args=[obj.pk]))
        return "—"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("requirement")


class ApplicationEventInline(admin.TabularInline):
    model = ApplicationEvent
    extra = 0
    can_delete = False
    readonly_fields = ("status", "note", "created_at")
    fields = ("status", "note", "created_at")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ServiceApplication)
class ServiceApplicationAdmin(admin.ModelAdmin):
    form = ApplicationAdminForm
    list_display = ("number_display", "client_name", "client_email", "service_title", "status", "currency", "total", "assigned_to", "estimated_delivery")
    list_filter = ("status", "currency", "offering__country")
    search_fields = ("client__first_name", "client__last_name", "client__email", "service_title")
    list_select_related = ("client", "assigned_to", "offering")
    readonly_fields = ("client", "offering", "service_title", "location_label", "currency", "subtotal", "tax_amount", "total", "payment_confirmed_at", "stripe_checkout_session", "stripe_payment_intent", "confirmation_sent_at", "terms_accepted_at", "answers", "notes", "created_at")
    fields = ("client", "offering", "service_title", "location_label", "status", "assigned_to", "estimated_delivery", "quoted_amount", "currency", "subtotal", "tax_amount", "total", "payment_confirmed_at", "stripe_checkout_session", "stripe_payment_intent", "confirmation_sent_at", "terms_accepted_at", "answers", "notes", "created_at")
    inlines = [ApplicationDocumentInline, ApplicationEventInline]

    @admin.display(description="Order")
    def number_display(self, obj):
        return obj.number

    @admin.display(description="Client")
    def client_name(self, obj):
        return obj.client.get_full_name() or obj.client.email

    @admin.display(description="Email")
    def client_email(self, obj):
        return obj.client.email

    def has_add_permission(self, request):
        return False

    def save_model(self, request, obj, form, change):
        previous = ServiceApplication.objects.get(pk=obj.pk) if change else None
        super().save_model(request, obj, form, change)
        if previous and previous.status != obj.status:
            ApplicationEvent.objects.create(application=obj, status=obj.status, note="Updated by Galiel staff")
            def send_notification():
                try:
                    if obj.status == "quoted":
                        text = f"Your quotation is ready: {obj.currency} {obj.quoted_amount} (total payable). Sign in and select Pay now from your process."
                    else:
                        text = f"Your process status changed to: {obj.get_status_display()}."
                    _notify_client(obj, "Process update", text)
                except Exception:
                    logger.exception("Failed to send case status email for %s", obj.pk)
            transaction.on_commit(send_notification)


@admin.register(ApplicationDocument)
class ApplicationDocumentAdmin(admin.ModelAdmin):
    form = ApplicationDocumentAdminForm
    list_display = ("application", "original_filename", "review_status", "is_deliverable", "is_invoice", "uploaded_at")
    search_fields = ("application__client__email", "application__service_title")
    readonly_fields = ("uploaded_at", "staff_preview")
    @admin.display(description="Private file")
    def staff_preview(self, obj):
        if obj and obj.pk:
            return format_html('<a href="{}" target="_blank" rel="noopener">Preview file</a>', reverse("staff_document_download", args=[obj.pk]))
        return "—"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)


@admin.register(ContactLead)
class ContactLeadAdmin(admin.ModelAdmin):
    list_display = ("lead_number", "full_name", "email", "country", "request_type", "status", "team_notified", "visitor_notified", "created_at")
    list_filter = ("status", "country", "team_notified", "visitor_notified", "created_at")
    search_fields = ("full_name", "email", "phone", "state_city", "request_type", "message")
    list_select_related = ("client", "conversation")
    list_per_page = 30
    readonly_fields = ("full_name", "email", "phone_code", "phone", "country", "state_city", "request_type",
                       "message", "privacy_consent_at", "attachment_link", "attachment_filename", "language",
                       "client", "conversation", "visitor_notified", "team_notified", "delivery_error", "created_at")
    fields = ("status", "full_name", "email", "phone_code", "phone", "country", "state_city",
              "request_type", "message", "attachment_link", "attachment_filename",
              "privacy_consent_at", "language", "client", "conversation",
              "visitor_notified", "team_notified", "delivery_error", "created_at")

    def has_add_permission(self, request):
        return False

    @admin.display(description="Lead")
    def lead_number(self, obj):
        return f"GL-{obj.pk:06d}"

    @admin.display(description="Private attachment")
    def attachment_link(self, obj):
        if obj and obj.pk and obj.attachment:
            return format_html('<a href="{}">Download attachment</a>',
                               reverse("staff_lead_attachment", args=[obj.pk]))
        return "No attachment"
