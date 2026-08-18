from django.urls import reverse


def user_dashboard(request):
    """Exposes user_dashboard_url so the header can link the avatar to the
    right dashboard for the logged-in user's role, from any page."""
    if not request.user.is_authenticated:
        return {}
    from .views import ROLE_DASHBOARD_URL_NAME
    url_name = ROLE_DASHBOARD_URL_NAME.get(request.user.role, 'core:home')
    return {'user_dashboard_url': reverse(url_name)}
