from django import template
from galiel_ops.models import Reminder
register=template.Library()

@register.simple_tag(takes_context=True)
def galiel_unread(context):
    request=context.get("request")
    if request is None or not request.user.is_authenticated:
        return 0
    return Reminder.objects.filter(user=request.user,dismissed=False,read_at__isnull=True).count()

@register.simple_tag(takes_context=True)
def ops_locale(context):
    """Same EN/ES/FR preference as the client portal, including language cookie."""
    request=context.get("request")
    if request is None:
        return "en"
    language=request.GET.get("lang") or request.COOKIES.get("galiel_lang")
    if not language and request.user.is_authenticated:
        try:
            language=request.user.profile.preferred_language
        except (AttributeError, Exception):
            language="en"
    return language if language in ("en","es","fr") else "en"
