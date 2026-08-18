from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm

from .models import User


def _field_input(attrs=None, **extra):
    base = {'class': 'field'}
    base.update(attrs or {})
    base.update(extra)
    return base


class RegisterForm(forms.ModelForm):
    full_name = forms.CharField(
        widget=forms.TextInput(attrs=_field_input(id='regName', placeholder='Enter your full name')),
    )
    mobile_number = forms.CharField(
        widget=forms.TextInput(attrs=_field_input(id='regMobile', placeholder='Enter 10 digit mobile number')),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs=_field_input(id='regEmail', placeholder='Enter your email address')),
    )
    password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs=_field_input(
            {'class': 'field js-password-input'}, id='regPassword', placeholder='Create a strong password',
        )),
    )
    confirm_password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs=_field_input(
            {'class': 'field js-password-input'}, id='regConfirm', placeholder='Confirm your password',
        )),
    )
    accept_terms = forms.BooleanField(required=True, error_messages={
        'required': 'You must accept the Terms & Conditions to create an account.',
    })

    class Meta:
        model = User
        fields = ['role', 'full_name', 'mobile_number', 'email']
        widgets = {
            'role': forms.HiddenInput(attrs={'id': 'regAccountType'}),
        }

    def clean_role(self):
        role = self.cleaned_data['role']
        if role not in User.PUBLIC_ROLES:
            raise forms.ValidationError('Select a valid account type.')
        return role

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean_mobile_number(self):
        mobile = self.cleaned_data['mobile_number'].strip()
        digits = mobile.replace('+', '').replace(' ', '')
        if not digits.isdigit() or len(digits) < 10:
            raise forms.ValidationError('Enter a valid mobile number.')
        return mobile

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.accepted_terms = True
        if commit:
            user.save()
        return user


class EmailLoginForm(forms.Form):
    """Shared by the public login page and the internal admin login page."""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs=_field_input(id='loginEmail', placeholder='Enter your registered email')),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs=_field_input(
            {'class': 'field js-password-input'}, id='loginPassword', placeholder='Enter your password',
        )),
    )

    allowed_roles = User.PUBLIC_ROLES
    generic_error = 'Invalid email or password. Please try again.'

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        if email and password:
            user = authenticate(self.request, username=email, password=password)
            if user is None or user.role not in self.allowed_roles:
                raise forms.ValidationError(self.generic_error)
            if not user.is_active:
                raise forms.ValidationError('This account has been deactivated.')
            cleaned_data['user'] = user
        return cleaned_data


class AdminLoginForm(EmailLoginForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs=_field_input(id='adminEmail', placeholder='Enter your email address')),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs=_field_input(
            {'class': 'field js-password-input'}, id='adminPassword', placeholder='Enter your password',
        )),
    )
    role = forms.ChoiceField(
        choices=[(User.Role.SUPER_ADMIN, 'Super Admin'), (User.Role.ADMIN, 'Admin')],
        widget=forms.HiddenInput(attrs={'id': 'adminRole'}),
    )
    allowed_roles = User.INTERNAL_ROLES

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        role = cleaned_data.get('role')
        if user and role and user.role != role:
            raise forms.ValidationError(self.generic_error)
        return cleaned_data


class ForgotPasswordForm(PasswordResetForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs=_field_input(id='fpEmail', placeholder='Enter your registered email')),
    )


class SetNewPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs=_field_input(
            {'class': 'field js-password-input js-strength-input'}, id='fpNewPassword', placeholder='Enter new password',
        )),
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs=_field_input(
            {'class': 'field js-password-input'}, id='fpConfirmPassword', placeholder='Confirm new password',
        )),
    )
