from django import template

register = template.Library()

@register.filter
def get_field(form, name):
    """Return form[name] or None if not available (safe for templates)."""
    try:
        return form[name]
    except Exception:
        return None