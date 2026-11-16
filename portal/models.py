import uuid
from pathlib import Path
from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    LANGUAGE_CHOICES = [
        ("en", "English"),
        ("es", "Español"),
        ("fr", "Français"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=40, blank=True)
    company = models.CharField(max_length=180, blank=True)
    tax_id = models.CharField(max_length=80, blank=True, default="")
    address = models.CharField(max_length=300, blank=True)  # Preserve legacy address
    street = models.CharField(max_length=180, blank=True, default="")
    street_number = models.CharField(max_length=30, blank=True, default="")
    unit = models.CharField(max_length=60, blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    state_region = models.CharField(max_length=100, blank=True, default="")
    postal_code = models.CharField(max_length=30, blank=True, default="")
    country = models.CharField(max_length=100, blank=True, default="")
    preferred_language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default="en")

    def __str__(self):
        return f"{self.user.username} profile"

def private_document_path(instance, filename):
    return f"client_documents/{instance.owner_id}/{uuid.uuid4().hex}.pdf"


class ClientDocument(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="client_documents")
    title = models.CharField(max_length=180)
    file = models.FileField(upload_to=private_document_path)
    original_filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.title


class ClientConversation(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name="galiel_conversations")
    subject = models.CharField(max_length=160)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.subject


class ClientMessage(models.Model):
    conversation = models.ForeignKey(ClientConversation, on_delete=models.CASCADE, related_name="entries")
    sender = models.ForeignKey(User, on_delete=models.PROTECT, related_name="galiel_sent_messages")
    body = models.TextField(max_length=5000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "pk"]

    def __str__(self):
        return f"Message in {self.conversation_id} from {self.sender_id}"


# Location-first service catalog; nothing is publicly priced until a manager publishes it.
class CatalogCountry(models.Model):
    code = models.CharField(max_length=2, primary_key=True)
    name_en = models.CharField(max_length=100)
    name_es = models.CharField(max_length=100)
    name_fr = models.CharField(max_length=100)

    class Meta:
        ordering = ["name_en"]
        verbose_name_plural = "Catalog countries"

    def __str__(self):
        return self.name_en


class CatalogRegion(models.Model):
    country = models.ForeignKey(CatalogCountry, on_delete=models.PROTECT, related_name="regions")
    slug = models.SlugField(max_length=80)
    name_en = models.CharField(max_length=120)
    name_es = models.CharField(max_length=120)
    name_fr = models.CharField(max_length=120)

    class Meta:
        ordering = ["name_en"]
        constraints = [models.UniqueConstraint(fields=["country", "slug"], name="catalog_region_unique")]

    def __str__(self):
        return f"{self.name_en}, {self.country.code}"


class CatalogMunicipality(models.Model):
    region = models.ForeignKey(CatalogRegion, on_delete=models.PROTECT, related_name="municipalities")
    slug = models.SlugField(max_length=90)
    name_en = models.CharField(max_length=130)
    name_es = models.CharField(max_length=130)
    name_fr = models.CharField(max_length=130)

    class Meta:
        ordering = ["name_en"]
        constraints = [models.UniqueConstraint(fields=["region", "slug"], name="catalog_municipality_unique")]

    def __str__(self):
        return f"{self.name_en}, {self.region.name_en}"


class CatalogService(models.Model):
    slug = models.SlugField(max_length=120, unique=True)
    title_en = models.CharField(max_length=180)
    title_es = models.CharField(max_length=180)
    title_fr = models.CharField(max_length=180)
    description_en = models.TextField(blank=True)
    description_es = models.TextField(blank=True)
    description_fr = models.TextField(blank=True)

    class Meta:
        ordering = ["title_en"]

    def __str__(self):
        return self.title_en


class ServiceOffering(models.Model):
    PRICE_TYPES = [
        ("fixed", "Fixed price"),
        ("starting", "Starting at"),
        ("quote", "Quotation required"),
    ]
    CURRENCIES = [("MXN", "MXN"), ("USD", "USD"), ("EUR", "EUR")]

    service = models.ForeignKey(CatalogService, on_delete=models.PROTECT, related_name="offerings")
    country = models.ForeignKey(CatalogCountry, on_delete=models.PROTECT, related_name="offerings")
    region = models.ForeignKey(CatalogRegion, null=True, blank=True, on_delete=models.PROTECT, related_name="offerings")
    municipality = models.ForeignKey(CatalogMunicipality, null=True, blank=True, on_delete=models.PROTECT, related_name="offerings")
    price_type = models.CharField(max_length=12, choices=PRICE_TYPES, default="quote")
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, choices=CURRENCIES, default="MXN")
    estimated_min_business_days = models.PositiveSmallIntegerField(null=True, blank=True)
    estimated_max_business_days = models.PositiveSmallIntegerField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    manager_notes = models.TextField(blank=True, help_text="Internal only; never shown to clients.")
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Starting-price services: optional payable deposit, not final price.")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Applicable checkout tax percentage configured by staff; do not assume IVA applies.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["country__name_en", "region__name_en", "municipality__name_en", "service__title_en"]
        constraints = [
            models.UniqueConstraint(
                fields=["service", "country", "region", "municipality"],
                name="catalog_offering_location_unique",
            ),
            models.CheckConstraint(
                check=models.Q(price__gte=0) | models.Q(price__isnull=True),
                name="catalog_price_nonnegative",
            ),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        errors = {}
        if self.region_id and self.region.country_id != self.country_id:
            errors["region"] = "Region must belong to the selected country."
        if self.municipality_id:
            if not self.region_id:
                errors["municipality"] = "Choose a region before a municipality."
            elif self.municipality.region_id != self.region_id:
                errors["municipality"] = "Municipality must belong to the selected region."
        if self.price_type in ("fixed", "starting") and self.price is None:
            errors["price"] = "A published price requires an amount."
        if (
            self.estimated_min_business_days is not None
            and self.estimated_max_business_days is not None
            and self.estimated_min_business_days > self.estimated_max_business_days
        ):
            errors["estimated_max_business_days"] = "Maximum time cannot be less than minimum time."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        location = self.municipality or self.region or self.country
        return f"{self.service} — {location}"


class ServiceRequirement(models.Model):
    KINDS = [("question", "Intake question"), ("document", "Required document")]
    offering = models.ForeignKey(ServiceOffering, on_delete=models.CASCADE, related_name="requirements")
    kind = models.CharField(max_length=10, choices=KINDS)
    label_en = models.CharField(max_length=220)
    label_es = models.CharField(max_length=220)
    label_fr = models.CharField(max_length=220)
    is_required = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "id"]

    def __str__(self):
        return self.label_en


def case_file_path(instance, filename):
    suffix = Path(filename).suffix.lower()
    return f"case_documents/{instance.application.client_id}/{instance.application_id}/{uuid.uuid4().hex}{suffix}"


class ServiceApplication(models.Model):
    STATUS = [
        ("draft", "Draft"),
        ("quote_requested", "Quote requested"),
        ("quoted", "Quote ready"),
        ("awaiting_payment", "Awaiting payment"),
        ("paid", "Paid"),
        ("under_review", "Under review"),
        ("missing_documents", "Missing documents"),
        ("submitted", "Submitted to authority"),
        ("in_process", "In process"),
        ("ready", "Ready / Delivered"),
        ("cancelled", "Cancelled"),
    ]
    client = models.ForeignKey(User, on_delete=models.PROTECT, related_name="galiel_applications")
    offering = models.ForeignKey(ServiceOffering, on_delete=models.PROTECT, related_name="applications")
    status = models.CharField(max_length=25, choices=STATUS, default="draft", db_index=True)
    step = models.PositiveSmallIntegerField(default=1)
    answers = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    service_title = models.CharField(max_length=180, blank=True)
    location_label = models.CharField(max_length=240, blank=True)
    currency = models.CharField(max_length=3, blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    quoted_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Staff-approved amount payable, including any tax.")
    estimated_delivery = models.DateField(null=True, blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="assigned_galiel_cases")
    conversation = models.OneToOneField(ClientConversation, null=True, blank=True, on_delete=models.SET_NULL, related_name="application")
    stripe_checkout_session = models.CharField(max_length=255, blank=True)
    stripe_payment_intent = models.CharField(max_length=255, blank=True)
    stripe_receipt_url = models.URLField(max_length=1000, blank=True)
    payment_confirmed_at = models.DateTimeField(null=True, blank=True)
    confirmation_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    @property
    def number(self):
        return f"GAL-{self.pk:06d}"

    def __str__(self):
        return f"{self.number} · {self.client.email} · {self.get_status_display()}"


class ApplicationDocument(models.Model):
    application = models.ForeignKey(ServiceApplication, on_delete=models.CASCADE, related_name="documents")
    requirement = models.ForeignKey(ServiceRequirement, on_delete=models.PROTECT, null=True, blank=True)
    original_filename = models.CharField(max_length=255)
    file = models.FileField(upload_to=case_file_path)
    content_type = models.CharField(max_length=40)
    size = models.PositiveIntegerField()
    is_deliverable = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["uploaded_at"]


class ApplicationEvent(models.Model):
    application = models.ForeignKey(ServiceApplication, on_delete=models.CASCADE, related_name="events")
    status = models.CharField(max_length=25, choices=ServiceApplication.STATUS)
    note = models.CharField(max_length=400, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "pk"]
