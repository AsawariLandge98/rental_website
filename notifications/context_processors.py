def unread_notifications(request):
    """Exposes unread_notifications_count for the dashboard topbar bell
    badge, on every page (mirrors accounts.context_processors.user_dashboard)."""
    if not request.user.is_authenticated:
        return {}
    return {'unread_notifications_count': request.user.notifications.filter(is_read=False).count()}
