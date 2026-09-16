from .models import SiteSettings


def site_settings(request):
    """Makes {{ site_settings }} available in every template — support
    phone/email and social links, the one real source now instead of the
    hardcoded/duplicated strings and dead `#` links this replaced."""
    return {'site_settings': SiteSettings.load()}
