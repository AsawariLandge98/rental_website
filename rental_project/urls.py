"""
URL configuration for rental_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from core.sitemaps import PropertySitemap, StaticViewSitemap
from core.views import robots_txt

SITEMAPS = {'static': StaticViewSitemap, 'properties': PropertySitemap}

urlpatterns = [
    path('sitemap.xml', sitemap, {'sitemaps': SITEMAPS}, name='sitemap'),
    path('robots.txt', robots_txt, name='robots_txt'),
    # dashboard.urls owns /admin/dashboard/... — must be tried before the
    # Django admin site below, whose catch-all view otherwise intercepts
    # any /admin/* path (redirecting non-Django-staff users to
    # /admin/login/) before it can ever reach our own admin dashboard.
    path('', include('core.urls')),
    path('properties/', include('properties.urls')),
    path('roommates/', include('roommates.urls')),
    path('hotels/', include('hotels.urls')),
    path('accounts/', include('accounts.urls')),
    # allauth owns just the Google OAuth handshake (initiate + callback) at
    # its own prefix — kept separate from accounts/ above so it can never
    # collide with our own real login/register/logout URLs there.
    path('social-auth/', include('allauth.urls')),
    path('', include('dashboard.urls')),
    path('tenant/dashboard/inquiries/', include('inquiries.urls')),
    path('tenant/dashboard/visits/', include('visits.urls')),
    path('tenant/dashboard/bookings/', include('bookings.urls')),
    path('tenant/dashboard/notifications/', include('notifications.urls')),
    path('tenant/dashboard/reviews/', include('reviews.urls')),
    path('owner/dashboard/subscription/', include('subscriptions.urls')),
    path('admin/', admin.site.urls),
]

if settings.DEBUG or not settings.CLOUD_STORAGE_CONFIGURED:
    # Django's own media serving is normally DEBUG-only (Django's docs
    # correctly call it unsuitable for real production traffic/security) —
    # but until real S3 credentials exist (CLOUD_STORAGE_CONFIGURED),
    # nothing else serves /media/ at all, so uploaded photos would 404
    # outright. This is a stopgap for a low-traffic deployment: perfectly
    # fine to keep serving media this way once S3 is configured too (the
    # condition then goes False and this block stops applying), but the
    # underlying local-disk storage still doesn't persist across Render
    # redeploys — turning on AWS_* in .env remains the real, permanent fix.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
