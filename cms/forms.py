from django import forms

from .models import FAQ


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


class FAQForm(StyledModelForm):
    class Meta:
        model = FAQ
        fields = ['question', 'answer', 'placement', 'order', 'is_published']
        widgets = {
            'answer': forms.Textarea(attrs={'rows': 4, 'maxlength': 1000}),
        }
