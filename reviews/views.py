from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from dashboard.decorators import tenant_required
from notifications.models import Notification, notify
from properties.models import Property
from visits.models import Visit
from .forms import ReviewForm
from .models import Review


@tenant_required
@require_POST
def submit_review(request, property_id):
    """Handles both a new review and editing an existing one — resubmitting
    the same form just updates the tenant's one review for this property
    (real UniqueConstraint enforces one review per tenant per property)."""
    property_obj = get_object_or_404(Property, pk=property_id, status=Property.Status.PUBLISHED)

    has_completed_visit = Visit.objects.filter(
        tenant=request.user, property=property_obj, status=Visit.Status.COMPLETED,
    ).exists()
    if not has_completed_visit:
        messages.error(request, 'You can only review a property after completing a visit to it.')
        return redirect('properties:detail', pk=property_id)

    existing_review = Review.objects.filter(tenant=request.user, property=property_obj).first()
    form = ReviewForm(request.POST, instance=existing_review)
    if form.is_valid():
        review = form.save(commit=False)
        review.tenant = request.user
        review.property = property_obj
        review.save()
        is_new = existing_review is None
        notify(
            property_obj.owner,
            f'{request.user.full_name} {"left a" if is_new else "updated their"} {review.rating}-star review on "{property_obj.title}".',
            category=Notification.Category.SYSTEM, url=reverse('properties:detail', args=[property_obj.pk]),
        )
    else:
        messages.error(request, ' '.join(e for errs in form.errors.values() for e in errs))
    return redirect('properties:detail', pk=property_id)
