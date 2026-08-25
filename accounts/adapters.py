from django.urls import reverse

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from .models import User


class RentoraAccountAdapter(DefaultAccountAdapter):
    """Only allauth's own post-login redirect resolution is used here — our
    real login/register views never call into allauth at all. This just
    sends a brand-new Google sign-up to the one real thing Google can't
    give us (date of birth) before landing on their dashboard."""

    def get_login_redirect_url(self, request):
        if request.session.pop('needs_profile_completion', False):
            return reverse('accounts:complete_profile')
        from .views import ROLE_DASHBOARD_URL_NAME
        url_name = ROLE_DASHBOARD_URL_NAME.get(request.user.role, 'core:home')
        return reverse(url_name)


class RentoraSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Maps a Google login onto our own email-based custom User model (no
    username field, no allauth signup form) instead of allauth's default
    username-based flow, and links to an existing account by email rather
    than erroring out or creating a duplicate."""

    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            return
        email = (sociallogin.account.extra_data.get('email') or '').strip().lower()
        if not email:
            return
        try:
            existing = User.objects.get(email=email)
        except User.DoesNotExist:
            return
        sociallogin.connect(request, existing)

    def populate_user(self, request, sociallogin, data):
        user = User()
        user.email = (data.get('email') or sociallogin.account.extra_data.get('email') or '').strip().lower()
        full_name = data.get('name') or ' '.join(filter(None, [data.get('first_name'), data.get('last_name')])).strip()
        user.full_name = full_name or (user.email.split('@')[0] if user.email else '')
        role = request.session.get('social_signup_role')
        user.role = role if role in User.PUBLIC_ROLES else User.Role.TENANT
        return user

    def save_user(self, request, sociallogin, form=None):
        user = sociallogin.user
        if not user.pk:
            if not user.full_name:
                user.full_name = (user.email or '').split('@')[0]
            if not user.role:
                user.role = User.Role.TENANT
            user.is_email_verified = True  # Google already verified this address
            user.set_unusable_password()
            user.save()
            request.session['needs_profile_completion'] = True
        request.session.pop('social_signup_role', None)
        return user
