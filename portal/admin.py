from django.contrib import admin

from .models import Profile, ClientConversation, ClientMessage, CatalogCountry, CatalogRegion, CatalogMunicipality, CatalogService, ServiceOffering, ServiceRequirement


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
        ("Commercial details", {"fields": ("price_type", "price", "currency", "estimated_min_business_days", "estimated_max_business_days")}),
        ("Visibility & internal notes", {"fields": ("is_published", "manager_notes")}),
    )
