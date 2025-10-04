from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """Filtre pour accéder à un dictionnaire avec une clé dynamique"""
    return dictionary.get(key)

@register.filter
def get_item(dictionary, key):
    """Filtre pour accéder à un dictionnaire avec une clé dynamique"""
    return dictionary.get(key)

@register.filter
def mul(value, arg):
    """Filtre pour multiplier une valeur par un argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def split(value, delimiter=','):
    """Filtre pour diviser une chaîne en liste"""
    try:
        return value.split(delimiter)
    except (AttributeError, TypeError):
        return []
