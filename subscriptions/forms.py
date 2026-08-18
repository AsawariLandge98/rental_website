from django import forms

from .models import SubscriptionPlan


class StyledModelForm(forms.ModelForm):
    """Same `.field` auto-styling as properties.forms.StyledModelForm."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        skip = (forms.CheckboxInput, forms.CheckboxSelectMultiple, forms.RadioSelect)
        for field in self.fields.values():
            if isinstance(field.widget, skip):
                continue
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing} field'.strip()


class SubscriptionPlanForm(StyledModelForm):
    class Meta:
        model = SubscriptionPlan
        fields = ['name', 'price', 'listing_limit', 'priority_listing', 'features', 'order', 'is_active']
        widgets = {
            'features': forms.Textarea(attrs={'rows': 4, 'placeholder': 'One feature per line'}),
        }
