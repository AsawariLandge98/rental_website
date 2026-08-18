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
from django.urls import include, path

urlpatterns = [
    # dashboard.urls owns /admin/dashboard/... — must be tried before the
    # Django admin site below, whose catch-all view otherwise intercepts
    # any /admin/* path (redirecting non-Django-staff users to
    # /admin/login/) before it can ever reach our own admin dashboard.
    path('', include('core.urls')),
    path('properties/', include('properties.urls')),
    path('roommates/', include('roommates.urls')),
    path('hotels/', include('hotels.urls')),
    path('accounts/', include('accounts.urls')),
    path('', include('dashboard.urls')),
    path('tenant/dashboard/inquiries/', include('inquiries.urls')),
    path('tenant/dashboard/visits/', include('visits.urls')),
    path('tenant/dashboard/notifications/', include('notifications.urls')),
    path('owner/dashboard/subscription/', include('subscriptions.urls')),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
