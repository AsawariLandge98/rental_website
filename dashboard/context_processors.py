PAGE_TITLES = {
    'owner': 'Dashboard', 'hotel': 'Dashboard',
    'my_listings': 'My Properties',
    'start_listing': 'Add New Property', 'manage_step': 'Add New Property', 'manage_preview': 'Add New Property',
    'owner_inquiries': 'Tenant Inquiries',
    'owner_visits': 'Property Visits',
    'plan_list': 'Subscription Plan',
    'owner_profile': 'My Profile',
    'owner_settings': 'Settings',
    'owner_help': 'Help & Support',
    'list': 'Notifications',
    'tenant': 'Dashboard',
    'tenant_saved': 'Saved Properties',
    'tenant_profile': 'My Profile',
    'tenant_settings': 'Settings',
    'tenant_help': 'Help & Support',
    'admin': 'Dashboard', 'super_admin': 'Dashboard',
    'admin_users': 'User Management',
    'admin_properties': 'Properties', 'admin_property_detail': 'Property Detail',
    'admin_inquiries': 'Inquiries',
    'admin_visits': 'Property Visits',
    'admin_payments': 'Payments',
    'admin_subscriptions': 'Subscription Plans',
    'admin_reports': 'Reports & Analytics',
    'admin_support': 'Support Tickets',
    'admin_cms': 'CMS Management',
    'admin_audit_logs': 'Audit Logs',
    'admin_internal_users': 'Admin Users',
    'admin_settings': 'Settings',
    'admin_profile': 'My Profile',
}


def dash_page_title(request):
    """Derives the topbar's page title/breadcrumb from the current URL name —
    same lookup-by-url_name pattern already used for sidebar active states —
    so individual dashboard views don't each need to set one explicitly."""
    if not request.resolver_match:
        return {}
    return {'dash_page_title': PAGE_TITLES.get(request.resolver_match.url_name, 'Dashboard')}
