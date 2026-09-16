from django import forms

from .models import Property, PropertyPhoto


class StyledModelForm(forms.ModelForm):
    """Applies the site's `.field` input class to every widget except
    checkboxes/radios/checkbox-lists, which each step template renders by
    hand as `.option-card` grids instead of Django's default widget markup."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        skip = (forms.CheckboxInput, forms.CheckboxSelectMultiple, forms.RadioSelect)
        for field in self.fields.values():
            if isinstance(field.widget, skip):
                continue
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing} field'.strip()


class CategoryForm(StyledModelForm):
    class Meta:
        model = Property
        fields = ['category']
        widgets = {'category': forms.RadioSelect}


class PropertyInfoForm(StyledModelForm):
    class Meta:
        model = Property
        fields = [
            'title', 'description', 'property_type', 'furnishing_status', 'property_age',
            'total_area', 'carpet_area', 'built_up_area', 'facing', 'floor_number', 'total_floors',
            'bedrooms', 'bathrooms', 'balconies', 'parking',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'parking': forms.RadioSelect,
        }


class LocationForm(StyledModelForm):
    class Meta:
        model = Property
        fields = ['state', 'district', 'city', 'area_locality', 'landmark', 'pincode', 'full_address']
        widgets = {
            'full_address': forms.Textarea(attrs={'rows': 2}),
        }
        help_texts = {
            'full_address': "Only shown publicly after you approve a tenant's inquiry.",
        }


class TenantPreferenceForm(StyledModelForm):
    tenant_preferences = forms.MultipleChoiceField(
        choices=Property.TenantPreference.choices, required=False, widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Property
        fields = ['tenant_preferences']


class RentDetailsForm(StyledModelForm):
    class Meta:
        model = Property
        fields = [
            'monthly_rent', 'nightly_rate', 'security_deposit', 'maintenance_charges',
            'electricity_charges', 'water_charges', 'no_brokerage',
        ]


class AvailabilityForm(StyledModelForm):
    class Meta:
        model = Property
        fields = ['available_from', 'minimum_stay', 'preferred_move_in_date', 'lease_duration']
        widgets = {
            'available_from': forms.DateInput(attrs={'type': 'date'}),
            'preferred_move_in_date': forms.DateInput(attrs={'type': 'date'}),
        }


class AmenitiesForm(StyledModelForm):
    class Meta:
        model = Property
        fields = ['amenities']
        widgets = {'amenities': forms.CheckboxSelectMultiple}


class ContactPreferenceForm(StyledModelForm):
    contact_preferences = forms.MultipleChoiceField(
        choices=Property.ContactPreference.choices, required=False, widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Property
        fields = ['contact_preferences']


class ListingPlanForm(StyledModelForm):
    class Meta:
        model = Property
        fields = ['listing_plan']
        widgets = {'listing_plan': forms.RadioSelect}


class PropertyPhotoForm(forms.ModelForm):
    class Meta:
        model = PropertyPhoto
        fields = ['image', 'caption']
