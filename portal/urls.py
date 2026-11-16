from django.contrib.auth import views as auth_views
from django.urls import path

from . import views, workflow_views

urlpatterns = [
    path("", views.home, name="home"),
    path("wordmark/", views.wordmark, name="wordmark"),
    path("register/", views.register, name="register"),
    path("register/complete/", views.registration_complete, name="registration_complete"),
    path("activate/<uidb64>/<token>/", views.activate_account, name="activate_account"),
    path("register/resend/", views.resend_activation, name="resend_activation"),
    path(
        "login/",
        views.ServiceAwareLoginView.as_view(),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="home"),
        name="logout",
    ),
    path("password-reset/", auth_views.PasswordResetView.as_view(
        template_name="portal/password_reset.html",
        email_template_name="portal/password_reset_email.txt",
        success_url="/password-reset/done/",
    ), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(
        template_name="portal/password_reset_done.html",
    ), name="password_reset_done"),
    path("password-reset/confirm/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="portal/password_reset_confirm.html",
        success_url="/password-reset/complete/",
    ), name="password_reset_confirm"),
    path("password-reset/complete/", auth_views.PasswordResetCompleteView.as_view(
        template_name="portal/password_reset_complete.html",
    ), name="password_reset_complete"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("services/start/", views.service_start, name="service_start"),
    path("services/", views.service_catalog, name="service_catalog"),
    path("services/api/catalog/", views.catalog_api, name="catalog_api"),
    path("services/<int:offering_id>/intake/", views.service_intake, name="service_intake"),
    path("services/<int:offering_id>/start/", workflow_views.application_start, name="application_start"),
    path("services/applications/<int:application_id>/step/<int:step>/", workflow_views.application_step, name="application_step"),
    path("services/applications/<int:application_id>/autosave/", workflow_views.application_autosave, name="application_autosave"),
    path("services/applications/<int:application_id>/upload/<int:requirement_id>/", workflow_views.application_upload, name="application_upload"),
    path("services/applications/<int:application_id>/remove/<int:document_id>/", workflow_views.application_delete_file, name="application_delete_file"),
    path("services/applications/<int:application_id>/download/<int:document_id>/", workflow_views.application_download, name="application_download"),
    path("services/applications/<int:application_id>/track/", workflow_views.application_track, name="application_track"),
    path("services/applications/<int:application_id>/receipt/", workflow_views.application_receipt, name="application_receipt"),
    path("services/applications/<int:application_id>/checkout/", workflow_views.application_checkout, name="application_checkout"),
    path("services/payment/webhook/", workflow_views.stripe_webhook, name="stripe_webhook"),
    path("profile/", views.profile, name="profile"),
    path("messages/", views.messages_inbox, name="messages_inbox"),
    path("messages/new/", views.conversation_new, name="conversation_new"),
    path("messages/<int:conversation_id>/", views.conversation_detail, name="conversation_detail"),
    path("documents/upload/", views.document_upload, name="document_upload"),
    path("documents/<int:document_id>/download/", views.document_download, name="document_download"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
]
