from django import forms, template

register = template.Library()


@register.filter
def times(number):
    """Usage: {% for _ in rating|times %} ... {% endfor %}"""
    return range(int(number))


@register.filter
def is_radio(bound_field):
    return isinstance(bound_field.field.widget, forms.RadioSelect)


@register.filter
def is_textarea(bound_field):
    return isinstance(bound_field.field.widget, forms.Textarea)
