"""Template tags for legacy frontend."""

from django import template

register = template.Library()


@register.filter
def format_time(minutes):
    """Format minutes into a human readable time string."""
    if not minutes:
        return ''
    minutes = int(minutes)
    if minutes < 60:
        return f'{minutes} min'
    hours = minutes // 60
    mins = minutes % 60
    if mins > 0:
        return f'{hours}h {mins}m'
    return f'{hours}h'


@register.filter
def in_list(value, collection):
    """Check if a value is in a collection (set, list, or tuple)."""
    return value in collection
