from datetime import datetime

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from dashboard.decorators import tenant_required
from notifications.models import Notification, notify
from properties.models import Property
from .models import Visit


@tenant_required
@require_POST
def schedule_visit(request, property_id):
    property_obj = get_object_or_404(Property, pk=property_id, status=Property.Status.PUBLISHED)
    scheduled_at = None
    raw = request.POST.get('scheduled_at', '').strip()
    if raw:
        try:
            scheduled_at = timezone.make_aware(datetime.fromisoformat(raw))
        except ValueError:
            scheduled_at = None
    if scheduled_at is None or scheduled_at < timezone.now():
        messages.error(request, 'Choose a valid, future date and time for your visit.')
        return redirect('properties:detail', pk=property_obj.pk)

    Visit.objects.create(tenant=request.user, property=property_obj, scheduled_at=scheduled_at)
    notify(
        request.user,
        f'Your visit request for "{property_obj.title}" on {scheduled_at:%d %b %Y, %I:%M %p} is awaiting the owner\'s approval.',
        category=Notification.Category.VISIT, url='/tenant/dashboard/visits/',
    )
    notify(
        property_obj.owner,
        f'{request.user.full_name} requested a visit to "{property_obj.title}" on {scheduled_at:%d %b %Y, %I:%M %p}.',
        category=Notification.Category.VISIT, url='/owner/dashboard/visits/',
    )
    messages.success(request, 'Visit requested! The owner will confirm or decline it shortly.')
    return redirect('properties:detail', pk=property_obj.pk)


@tenant_required
def my_visits(request):
    visits = request.user.visits.select_related('property', 'property__owner').prefetch_related('property__photos')
    return render(request, 'dashboard/my_visits.html', {'visits': visits})


@tenant_required
@require_POST
def cancel_visit(request, pk):
    visit = get_object_or_404(Visit, pk=pk, tenant=request.user)
    # Only pending/scheduled visits are cancellable — same states the UI's
    # own Cancel button is gated on. Without this, a completed visit could
    # be retroactively cancelled via a direct POST, undermining it as a
    # real "this visit actually happened" record.
    if visit.status in (Visit.Status.PENDING, Visit.Status.SCHEDULED):
        visit.status = Visit.Status.CANCELLED
        visit.save(update_fields=['status'])
        messages.success(request, 'Visit cancelled.')
    return redirect('visits:my_visits')
