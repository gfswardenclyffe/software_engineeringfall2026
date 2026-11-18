"""Idempotent due-soon reminder mailer, designed for one daily cron invocation."""
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from galiel_ops.models import Reminder
from galiel_ops.notifications import send_reminder_copy

class Command(BaseCommand):
    help = "Mail undismissed due-soon reminders once each (default 7 days ahead)."

    def add_arguments(self, parser):
        parser.add_argument("--days",type=int,default=7)
        parser.add_argument("--dry-run",action="store_true")

    def handle(self,*args,**options):
        days=options["days"]
        if days<0 or days>90:
            raise ValueError("--days must be between 0 and 90")
        today=timezone.localdate()
        qs=(Reminder.objects.filter(due_date__isnull=False,due_date__lte=today+timedelta(days=days),
             dismissed=False,due_notice_sent_at__isnull=True,user__is_active=True)
            .select_related("user").order_by("due_date","pk"))
        ids=list(qs.values_list("pk",flat=True))
        self.stdout.write(f"Eligible reminders: {len(ids)}")
        if options["dry_run"]:
            return
        success=0
        for pk in ids:
            if send_reminder_copy(pk,due_notice=True):
                success+=1
        self.stdout.write(f"Due-soon reminder emails sent: {success}; skipped/failed: {len(ids)-success}")
