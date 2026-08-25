from django.conf import settings
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import (
    AdminLoginForm, CompleteProfileForm, EmailLoginForm, ForgotPasswordForm, RegisterForm, SetNewPasswordForm,
)
from .models import User

ACCOUNT_TYPES = [
    {
        "key": "owner",
        "icon": "house",
        "title": "Property Owner",
        "text": "List your property and connect with tenants.",
    },
    {
        "key": "tenant",
        "icon": "users",
        "title": "Tenant / Renter",
        "text": "Find your perfect rental property hassle-free.",
    },
    {
        "key": "hotel",
        "icon": "building",
        "title": "Hotel / Homestay Owner",
        "text": "List your hotel, homestay or guest house for bookings.",
    },
]

REGISTER_PERKS = [
    {"icon": "shield-check", "title": "Real Listings, Real Owners", "text": "Every listing is posted directly by its actual owner — no middlemen."},
    {"icon": "key", "title": "Zero Brokerage", "text": "Connect directly with owners and save your hard-earned money."},
    {"icon": "chat", "title": "Direct Communication", "text": "Talk directly with owners and schedule visits easily."},
    {"icon": "lock", "title": "Secure & Trusted", "text": "Your data is protected with industry-standard security."},
]

FORGOT_PASSWORD_TRUST = [
    {"icon": "lock", "title": "Secure & Encrypted", "text": "All data is encrypted and protected"},
    {"icon": "envelope", "title": "Quick & Easy", "text": "Reset your password in just a few steps"},
    {"icon": "headset", "title": "24/7 Support", "text": "Need help? Contact our support team"},
    {"icon": "lock", "title": "Privacy First", "text": "Your information is always secure"},
]

ADMIN_LOGIN_FEATURES = [
    {"icon": "shield-check", "title": "Secure & Protected", "text": "Industry standard security to keep our platform and users safe."},
    {"icon": "users", "title": "Role-Based Access", "text": "Different permissions for Super Admin and Admin accounts."},
    {"icon": "bar-chart", "title": "Complete Control", "text": "Manage users, properties, subscriptions and platform operations."},
    {"icon": "clock", "title": "Activity Monitoring", "text": "All activities are logged and monitored for full transparency."},
]

# Where each role lands after login/registration. Tenant and Owner/Hotel
# dashboards are real; Admin/Super Admin are still placeholder pages until
# Parts 9-10 of the workflow doc are built.
ROLE_DASHBOARD_URL_NAME = {
    User.Role.TENANT: 'dashboard:tenant',
    User.Role.OWNER: 'dashboard:owner',
    User.Role.HOTEL: 'dashboard:hotel',
    User.Role.ADMIN: 'dashboard:admin',
    User.Role.SUPER_ADMIN: 'dashboard:super_admin',
}


def _redirect_for_role(role):
    return redirect(ROLE_DASHBOARD_URL_NAME.get(role, 'core:home'))


def _safe_next_url(request):
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return next_url
    return None


def login_view(request):
    if request.user.is_authenticated:
        return _redirect_for_role(request.user.role)

    if request.method == 'POST':
        form = EmailLoginForm(request.POST, request=request)
        if form.is_valid():
            user = form.cleaned_data['user']
            auth_login(request, user)
            next_url = _safe_next_url(request)
            if next_url:
                return redirect(next_url)
            return _redirect_for_role(user.role)
    else:
        form = EmailLoginForm(request=request)

    return render(request, "accounts/login.html", {
        "form": form, "google_oauth_configured": settings.GOOGLE_OAUTH_CONFIGURED,
    })


def register(request):
    if request.user.is_authenticated:
        return _redirect_for_role(request.user.role)

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f'Welcome to Rentora, {user.full_name}!')
            return _redirect_for_role(user.role)
    else:
        form = RegisterForm(initial={'role': request.GET.get('type', 'tenant')})

    context = {
        "form": form,
        "account_types": ACCOUNT_TYPES,
        "perks": REGISTER_PERKS,
        "google_oauth_configured": settings.GOOGLE_OAUTH_CONFIGURED,
    }
    return render(request, "accounts/register.html", context)


def google_login_start(request):
    """Stashes the intended account type in the session, then hands off to
    allauth's real Google OAuth flow. Kept as our own real URL (rather than
    linking straight to allauth's) so "Continue with Google" from the
    Become a Host flow can arrive as an Owner, same as the real register
    form already supports via ?type=owner."""
    if not settings.GOOGLE_OAUTH_CONFIGURED:
        messages.error(request, "Google sign-in isn't set up yet. Please use email and password for now.")
        return redirect('accounts:register')

    role = request.GET.get('type', User.Role.TENANT)
    if role in User.PUBLIC_ROLES:
        request.session['social_signup_role'] = role
    return redirect(reverse('google_login'))


def complete_profile(request):
    if not request.user.is_authenticated:
        return redirect('accounts:login')

    if request.method == 'POST':
        form = CompleteProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Welcome to Rentora, {request.user.full_name}!')
            return _redirect_for_role(request.user.role)
    else:
        form = CompleteProfileForm(instance=request.user)

    return render(request, "accounts/complete_profile.html", {"form": form})


@require_POST
def logout_view(request):
    was_internal = request.user.is_authenticated and request.user.is_internal
    auth_logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('accounts:admin_login' if was_internal else 'accounts:login')


def admin_login(request):
    if request.user.is_authenticated and request.user.is_internal:
        return _redirect_for_role(request.user.role)

    if request.method == 'POST':
        form = AdminLoginForm(request.POST, request=request)
        if form.is_valid():
            user = form.cleaned_data['user']
            auth_login(request, user)
            return _redirect_for_role(user.role)
    else:
        form = AdminLoginForm(request=request, initial={'role': User.Role.SUPER_ADMIN})

    context = {
        "form": form,
        "features": ADMIN_LOGIN_FEATURES,
    }
    return render(request, "accounts/admin_login.html", context)


# ---------------------------------------------------------------------------
# Forgot password (Django's built-in token-based flow). Email is printed to
# the runserver console in dev since no real SMTP/SMS provider is wired up
# yet — see settings.EMAIL_BACKEND.
# ---------------------------------------------------------------------------

class ForgotPasswordView(auth_views.PasswordResetView):
    template_name = 'accounts/forgot_password.html'
    email_template_name = 'accounts/emails/password_reset_email.txt'
    subject_template_name = 'accounts/emails/password_reset_subject.txt'
    form_class = ForgotPasswordForm
    success_url = reverse_lazy('accounts:password_reset_done')
    extra_context = {'trust_items': FORGOT_PASSWORD_TRUST}


class ForgotPasswordDoneView(auth_views.PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'


class ForgotPasswordConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    form_class = SetNewPasswordForm
    success_url = reverse_lazy('accounts:password_reset_complete')


class ForgotPasswordCompleteView(auth_views.PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'
