from django.urls import path
from . import views

urlpatterns = [
    path("updates/", views.announcement_list, name="galiel_announcements"),
    path("alerts/", views.reminder_list, name="galiel_reminders"),
    path("alerts/count/", views.unread_count, name="galiel_unread_count"),
    path("alerts/<int:reminder_id>/read/", views.reminder_read, name="galiel_reminder_read"),
    path("alerts/<int:reminder_id>/dismiss/", views.reminder_dismiss, name="galiel_reminder_dismiss"),
    path("services/applications/<int:application_id>/delete-draft/",views.delete_draft,name="galiel_delete_draft"),
    path("services/applications/<int:application_id>/delete-draft-file/<int:document_id>/",views.delete_draft_file,name="galiel_delete_draft_file"),
    path("services/applications/<int:application_id>/request-invoice/",views.request_invoice,name="galiel_request_invoice"),
    path("profile/request-deletion/",views.request_account_deletion,name="galiel_request_account_deletion"),
    path("profile/fiscal/",views.fiscal_profile,name="galiel_fiscal_profile"),
    path("help/services/",views.help_services,name="galiel_help_services"),
    path("help/options/",views.help_choices,name="galiel_help_choices"),
    path("help/requirements/<int:offering_id>/",views.help_requirements,name="galiel_help_requirements"),
    path("help/my-processes/",views.help_my_processes,name="galiel_help_processes"),
]
