from django import template
from galiel_ops.models import Reminder
register=template.Library()

@register.simple_tag(takes_context=True)
def galiel_unread(context):
    request=context.get("request")
    if request is None or not request.user.is_authenticated:
        return 0
    return Reminder.objects.filter(user=request.user,dismissed=False,read_at__isnull=True).count()
