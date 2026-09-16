from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

from accounts.models import OwnerProfile, TenantProfile, User
from .models import SupportTicket


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


class AccountBasicsForm(StyledModelForm):
    class Meta:
        model = User
        fields = ['full_name', 'mobile_number']


class TenantProfileForm(StyledModelForm):
    class Meta:
        model = TenantProfile
        fields = [
            'profile_photo', 'gender', 'date_of_birth', 'occupation', 'about',
            'preferred_city', 'preferred_budget_min', 'preferred_budget_max',
            'preferred_property_type', 'furnishing_preference', 'tenant_type', 'move_in_time',
        ]
        widgets = {
            'about': forms.Textarea(attrs={'rows': 3, 'maxlength': 300}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }


class NotificationPreferencesForm(StyledModelForm):
    class Meta:
        model = TenantProfile
        fields = [
            'email_notifications', 'sms_notifications', 'visit_reminders',
            'push_notifications', 'new_property_alerts', 'offers_updates',
        ]


class PrivacyPreferencesForm(StyledModelForm):
    class Meta:
        model = TenantProfile
        fields = ['show_profile_to_owners', 'allow_owner_contact']


class LanguageForm(StyledModelForm):
    class Meta:
        model = TenantProfile
        fields = ['language']


class OwnerNotificationPreferencesForm(StyledModelForm):
    class Meta:
        model = OwnerProfile
        fields = [
            'email_notifications', 'sms_notifications', 'new_inquiry_alerts',
            'visit_reminders', 'push_notifications', 'offers_updates',
        ]


class OwnerPrivacyPreferencesForm(StyledModelForm):
    class Meta:
        model = OwnerProfile
        fields = ['show_contact_to_tenants', 'allow_tenant_contact']


class OwnerLanguageForm(StyledModelForm):
    class Meta:
        model = OwnerProfile
        fields = ['language']


class SupportTicketForm(StyledModelForm):
    class Meta:
        model = SupportTicket
        fields = ['subject', 'category', 'description', 'attachment']
        widgets = {'description': forms.Textarea(attrs={'rows': 5, 'maxlength': 1000})}


class AdminCreateForm(StyledModelForm):
    """Super Admin creates another internal-role account directly (no
    self-registration path exists for Admin/Super Admin — see Feature 01).
    Deliberately never sets is_staff/is_superuser: Django's own /admin/
    site access is a separate, lower-level system this form doesn't grant."""

    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['full_name', 'email', 'mobile_number', 'role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].choices = [
            (User.Role.ADMIN, User.Role.ADMIN.label),
            (User.Role.SUPER_ADMIN, User.Role.SUPER_ADMIN.label),
        ]

    def clean(self):
        cleaned = super().clean()
        password1, password2 = cleaned.get('password1'), cleaned.get('password2')
        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Passwords don't match.")
        elif password1:
            try:
                validate_password(password1)
            except ValidationError as exc:
                self.add_error('password1', exc)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user
