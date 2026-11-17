# Galiel data model (Mermaid UML)

```mermaid
classDiagram
  class User
  class Profile
  class FiscalProfile {
    rfc
    razon_social
    regimen_fiscal
    uso_cfdi
    invoice_email
  }
  class ServiceApplication {
    status
    invoice_requested
    notes
  }
  class ApplicationDocument
  class Announcement {
    title_en
    title_es
    title_fr
    body_en
    body_es
    body_fr
    category
    published_at
    expires_at
  }
  class Reminder {
    kind
    message
    due_date
    read_at
    dismissed
    emailed_at
  }
  class AccountDeletionRequest {
    status
    requested_at
  }
  class InvoiceRequest {
    requested_at
    staff_notified_at
    handled_at
  }
  User "1" -- "1" Profile
  User "1" -- "0..1" FiscalProfile
  User "1" -- "*" ServiceApplication
  User "1" -- "*" Reminder
  User "1" -- "*" AccountDeletionRequest
  User "0..1" <-- "*" Announcement : author
  ServiceApplication "0..1" <-- "*" Reminder
  ServiceApplication "1" --> "*" ApplicationDocument
  ServiceApplication "1" -- "0..1" InvoiceRequest
```

## Flow
- Admin status updates -> on-commit reminder creation and email.
- Cron -> due date window + emailed_at idempotence -> SMTP.
- Client endpoints -> filtered by request.user -> render/POST updates.
- Database -> private snapshot; uploads -> daily private tar archive.
- No automatic invoice generation or Stripe checkout.
