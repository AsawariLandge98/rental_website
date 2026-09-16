from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from dashboard.decorators import tenant_required
from notifications.models import Notification, notify
from properties.models import Property
from .models import Inquiry, InquiryReply


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
    notify(
        property_obj.owner, f'{request.user.full_name} sent an inquiry about "{property_obj.title}".',
        category=Notification.Category.INQUIRY, url='/owner/dashboard/inquiries/',
    )
    messages.success(request, 'Inquiry sent — the owner\'s contact details are shown on this page.')
    return redirect('properties:detail', pk=property_obj.pk)


@tenant_required
def my_inquiries(request):
    inquiries = request.user.inquiries.select_related('property', 'property__owner').prefetch_related('property__photos')
    return render(request, 'dashboard/my_inquiries.html', {'inquiries': inquiries})


@tenant_required
def inquiry_detail(request, pk):
    inquiry = get_object_or_404(
        Inquiry.objects.select_related('property', 'property__owner'), pk=pk, tenant=request.user,
    )
    if request.method == 'POST':
        body = request.POST.get('message', '').strip()
        if body:
            InquiryReply.objects.create(inquiry=inquiry, sender=request.user, message=body)
            notify(
                inquiry.property.owner, f'{request.user.full_name} replied about "{inquiry.property.title}".',
                category=Notification.Category.INQUIRY, url=f'/owner/dashboard/inquiries/{inquiry.pk}/',
            )
            return redirect('inquiries:inquiry_detail', pk=inquiry.pk)

    replies = inquiry.replies.select_related('sender')
    return render(request, 'dashboard/inquiry_detail.html', {'inquiry': inquiry, 'replies': replies})


@tenant_required
@require_POST
def close_inquiry(request, pk):
    inquiry = get_object_or_404(Inquiry, pk=pk, tenant=request.user)
    inquiry.status = Inquiry.Status.CLOSED
    inquiry.save(update_fields=['status'])
    return redirect('inquiries:my_inquiries')
