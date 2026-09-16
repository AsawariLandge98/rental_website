from django import forms

from .models import RoommatePosting


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


class RoommatePostingForm(StyledModelForm):
    class Meta:
        model = RoommatePosting
        fields = [
            'posting_type', 'photo', 'room_type', 'city', 'area_locality', 'monthly_rent',
            'gender_preference', 'occupation', 'roommates_needed', 'move_in_date', 'description',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'maxlength': 600}),
            'move_in_date': forms.DateInput(attrs={'type': 'date'}),
        }
