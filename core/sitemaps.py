from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from properties.models import Property


class StaticViewSitemap(Sitemap):
    """The site's real, always-reachable public pages — no auth-gated
    dashboard routes, no dead placeholder pages."""

    priority = 0.7
    changefreq = 'weekly'

    def items(self):
        return [
            'core:home', 'core:about', 'core:contact', 'core:become_host',
            'properties:search', 'roommates:list', 'hotels:list',
        ]

    def location(self, item):
        return reverse(item)


class PropertySitemap(Sitemap):
    """Every real, currently published property listing."""

    changefreq = 'daily'
    priority = 0.9

    def items(self):
        return Property.objects.filter(status=Property.Status.PUBLISHED)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('properties:detail', args=[obj.pk])
