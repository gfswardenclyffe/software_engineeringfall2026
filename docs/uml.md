# Galiel — UML and system interactions

All diagrams describe the deployed client-portal functionality. Payments and fee-import automation are intentionally on hold.

## Use-case diagram (Mermaid)

```mermaid
flowchart LR
  Client["👤 Client"]:::actor
  Staff["👤 Authorized staff"]:::actor
  Cron["⏰ Daily scheduled task"]:::actor
  subgraph Galiel["Galiel client portal"]
    Register(["Register and sign in"])
    Services(["Browse administrative services"])
    Start(["Create and manage application"])
    Docs(["Upload, view, or remove draft documents"])
    Messages(["Message staff"])
    Track(["Track process status"])
    Updates(["Read news and updates"])
    Remind(["Read and dismiss reminders"])
    Delete(["Delete own draft"])
    Invoice(["Request a manual invoice"])
    Account(["Edit profile and request deletion"])
    Publish(["Manage announcements and reminders"])
    Backup(["Create private SQLite + uploads backup"])
    Email(["Send due-soon email alerts"])
  end
  Client --> Register & Services & Start & Docs & Messages & Track & Updates & Remind & Delete & Invoice & Account
  Staff --> Publish
  Cron --> Email & Backup
  Publish -. creates client notice .-> Remind
  Start -. generates status .-> Track
  classDef actor fill:#f2f1ec,stroke:#161616,color:#161616;
```

## Class diagram

```mermaid
classDiagram
  class User {
    +id
    +email
    +is_staff
  }
  class Profile {
    +preferred_language
    +phone
    +company
  }
  class CatalogService {
    +title_en
    +title_es
    +title_fr
  }
  class ServiceOffering {
    +country
    +is_published
  }
  class ServiceApplication {
    +status
    +step
    +answers
    +notes
    +number
  }
  class ApplicationDocument {
    +original_filename
    +file
    +review_status
    +is_deliverable
  }
  class Announcement {
    +title_en
    +title_es
    +title_fr
    +body_en
    +body_es
    +body_fr
    +category
    +published_at
    +expires_at
  }
  class Reminder {
    +kind
    +message
    +due_date
    +read_at
    +dismissed
    +emailed_at
  }
  class AccountDeletionRequest {
    +status
    +requested_at
    +handled_at
  }
  class FiscalProfile {
    +rfc
    +razon_social
    +regimen_fiscal
    +uso_cfdi
    +invoice_email
  }
  class InvoiceRequest {
    +requested_at
    +staff_notified_at
    +handled_at
  }
  User "1" --> "0..1" Profile : client profile
  User "1" --> "0..1" FiscalProfile : optional tax data
  User "1" --> "*" ServiceApplication : owns
  User "1" --> "*" Reminder : receives
  User "1" --> "*" AccountDeletionRequest : requests
  User "0..1" --> "*" Announcement : authors
  CatalogService "1" --> "*" ServiceOffering
  ServiceOffering "1" --> "*" ServiceApplication
  ServiceApplication "1" --> "*" ApplicationDocument
  ServiceApplication "0..1" --> "*" Reminder
  ServiceApplication "1" --> "0..1" InvoiceRequest
```

## Sequence diagram: staff requests a document

```mermaid
sequenceDiagram
  actor Staff
  participant Admin as Django Admin
  participant App as ServiceApplication
  participant Signal as galiel_ops signals
  participant DB as SQLite
  participant Mail as SMTP
  actor Client
  Staff->>Admin: Update application status to missing_documents
  Admin->>App: Save modified status
  App->>Signal: post_save signal
  Signal->>DB: Create client-owned Reminder
  DB-->>Signal: Reminder ID
  Signal->>Mail: Email copy after DB commit
  Mail-->>Client: Document-request notification
  Client->>DB: Read own reminders (authenticated)
  DB-->>Client: Reminder and status
  Client->>DB: Upload file to owned application
```

## Security boundaries

Private application, document, reminder and invoice-request queries must always be scoped to the authenticated owner. Staff-only administration uses Django staff permissions. A missing/expired announcement is excluded by publication windows. The daily backup command only archives an allowlisted set of private upload directories.
