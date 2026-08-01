from django import template

register = template.Library()


@register.filter
def times(number):
    """Usage: {% for _ in rating|times %} ... {% endfor %}"""
    return range(int(number))
