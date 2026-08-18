from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from dashboard.decorators import tenant_required
from notifications.models import Notification, notify
from properties.models import Property
from .models import Inquiry


@tenant_required
@require_POST
def send_inquiry(request, property_id):
    property_obj = get_object_or_404(Property, pk=property_id, status=Property.Status.PUBLISHED)
    Inquiry.objects.create(
        tenant=request.user, property=property_obj, message=request.POST.get('message', '').strip(),
    )
    notify(
        request.user, f'Your inquiry for "{property_obj.title}" has been sent to the owner.',
        category=Notification.Category.INQUIRY, url='/tenant/dashboard/inquiries/',
    )
    messages.success(request, 'Inquiry sent — the owner\'s contact details are shown on this page.')
    return redirect('properties:detail', pk=property_obj.pk)


@tenant_required
def my_inquiries(request):
    inquiries = request.user.inquiries.select_related('property', 'property__owner').prefetch_related('property__photos')
    return render(request, 'dashboard/my_inquiries.html', {'inquiries': inquiries})


@tenant_required
@require_POST
def close_inquiry(request, pk):
    inquiry = get_object_or_404(Inquiry, pk=pk, tenant=request.user)
    inquiry.status = Inquiry.Status.CLOSED
    inquiry.save(update_fields=['status'])
    messages.success(request, 'Inquiry closed.')
    return redirect('inquiries:my_inquiries')
