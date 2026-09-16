from datetime import date

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from dashboard.decorators import tenant_required
from notifications.models import Notification, notify
from properties.models import Property
from .models import Booking


def _dates_overlap(check_in, check_out, other_check_in, other_check_out):
    return check_in < other_check_out and other_check_in < check_out


@tenant_required
@require_POST
def request_booking(request, property_id):
    property_obj = get_object_or_404(
        Property, pk=property_id, status=Property.Status.PUBLISHED, category__in=Property.HOTEL_CATEGORIES,
    )
    check_in = request.POST.get('check_in', '')
    check_out = request.POST.get('check_out', '')
    guests = request.POST.get('guests', '1')

    try:
        check_in = date.fromisoformat(check_in)
        check_out = date.fromisoformat(check_out)
        guests = max(1, int(guests))
    except (ValueError, TypeError):
        messages.error(request, 'Enter a valid check-in date, check-out date and guest count.')
        return redirect('properties:detail', pk=property_obj.pk)

    if check_in < date.today():
        messages.error(request, 'Check-in date cannot be in the past.')
        return redirect('properties:detail', pk=property_obj.pk)
    if check_out <= check_in:
        messages.error(request, 'Check-out date must be after check-in.')
        return redirect('properties:detail', pk=property_obj.pk)

    confirmed = Booking.objects.filter(property=property_obj, status=Booking.Status.CONFIRMED)
    if any(_dates_overlap(check_in, check_out, b.check_in, b.check_out) for b in confirmed):
        messages.error(request, 'Those dates are already booked — try a different range.')
        return redirect('properties:detail', pk=property_obj.pk)

    Booking.objects.create(
        tenant=request.user, property=property_obj, check_in=check_in, check_out=check_out,
        guests=guests, message=request.POST.get('message', '').strip(),
    )
    notify(
        request.user, f'Your booking request for "{property_obj.title}" has been sent to the host.',
        category=Notification.Category.VISIT, url='/tenant/dashboard/bookings/',
    )
    notify(
        property_obj.owner, f'{request.user.full_name} requested to book "{property_obj.title}".',
        category=Notification.Category.VISIT, url='/owner/dashboard/bookings/',
    )
    return redirect('properties:detail', pk=property_obj.pk)


@tenant_required
def my_bookings(request):
    bookings = request.user.bookings.select_related('property', 'property__owner').prefetch_related('property__photos')
    return render(request, 'dashboard/my_bookings.html', {'bookings': bookings})


@tenant_required
@require_POST
def cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk, tenant=request.user)
    if booking.status in (Booking.Status.PENDING, Booking.Status.CONFIRMED):
        booking.status = Booking.Status.CANCELLED
        booking.save(update_fields=['status'])
    return redirect('bookings:my_bookings')
