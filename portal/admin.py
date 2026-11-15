from django.contrib import admin

from .models import Profile, ClientConversation, ClientMessage


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
