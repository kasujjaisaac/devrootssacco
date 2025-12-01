from django import template

register = template.Library()

@register.filter
def has_group(user, group_name):
    """Returns True if the user belongs to the given group."""
    return user.groups.filter(name=group_name).exists()
