from urllib.parse import quote

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import RoommatePostingForm
from .models import RoommatePosting

BUDGET_OPTIONS = [
    ('0-7000', 'Under ₹7,000'),
    ('7000-9000', '₹7,000 - ₹9,000'),
    ('9000-', 'Above ₹9,000'),
]


def _phone_digits(mobile_number):
    """Same normalization as properties.views._phone_digits — kept as its
    own small copy rather than a cross-app import, since a roommate posting
    isn't a Property and this app has no other reason to depend on it."""
    digits = ''.join(ch for ch in mobile_number if ch.isdigit())
    if len(digits) == 10:
        digits = '91' + digits
    return digits


def _poster_contact_options(posting):
    """Real Call / WhatsApp / Email links for the poster — visible
    directly, no inquiry-approval gate, same pattern as property owner
    contact (properties.views._owner_contact_options)."""
    poster = posting.poster
    options = []
    if poster.mobile_number:
        digits = _phone_digits(poster.mobile_number)
        options.append({
            'type': 'call', 'icon': 'phone', 'label': 'Call',
            'sublabel': poster.mobile_number, 'href': f'tel:+{digits}',
        })
        message = quote(f'Hi, I saw your roommate post on Rentora ("{posting.room_type}" in {posting.city}).')
        options.append({
            'type': 'whatsapp', 'icon': 'whatsapp', 'label': 'WhatsApp',
            'sublabel': 'Chat instantly', 'href': f'https://wa.me/{digits}?text={message}',
        })
    if poster.email:
        options.append({
            'type': 'email', 'icon': 'envelope', 'label': 'Email',
            'sublabel': poster.email, 'href': f'mailto:{poster.email}',
        })
    return options


def roommate_list(request):
    queryset = RoommatePosting.objects.filter(is_active=True).select_related('poster')

    selected_type = request.GET.get('type', '')
    selected_gender = request.GET.get('gender', '')
    selected_budget = request.GET.get('budget', '')
    selected_q = request.GET.get('q', '').strip()

    if selected_type in RoommatePosting.PostingType.values:
        queryset = queryset.filter(posting_type=selected_type)
    if selected_gender in RoommatePosting.Gender.values:
        queryset = queryset.filter(gender_preference=selected_gender)
    if selected_budget:
        lo_str, _, hi_str = selected_budget.partition('-')
        lo = int(lo_str) if lo_str else 0
        hi = int(hi_str) if hi_str else None
        queryset = queryset.filter(monthly_rent__gte=lo)
        if hi is not None:
            queryset = queryset.filter(monthly_rent__lte=hi)
    if selected_q:
        queryset = queryset.filter(Q(city__icontains=selected_q) | Q(area_locality__icontains=selected_q))

    context = {
        "roommates": queryset,
        "result_count": queryset.count(),
        "posting_type_options": RoommatePosting.PostingType.choices,
        "gender_options": RoommatePosting.Gender.choices,
        "budget_options": BUDGET_OPTIONS,
        "selected_type": selected_type,
        "selected_gender": selected_gender,
        "selected_budget": selected_budget,
        "selected_q": selected_q,
    }
    return render(request, "roommates/list.html", context)


def roommate_detail(request, pk):
    posting = get_object_or_404(RoommatePosting.objects.select_related('poster'), pk=pk, is_active=True)
    is_owner = request.user.is_authenticated and request.user.pk == posting.poster_id
    context = {
        "posting": posting,
        "contact_options": _poster_contact_options(posting),
        "is_owner": is_owner,
    }
    return render(request, "roommates/detail.html", context)


@login_required
def roommate_create(request):
    if request.method == 'POST':
        form = RoommatePostingForm(request.POST, request.FILES)
        if form.is_valid():
            posting = form.save(commit=False)
            posting.poster = request.user
            posting.save()
            return redirect('roommates:detail', pk=posting.pk)
    else:
        form = RoommatePostingForm()
    return render(request, "roommates/form.html", {"form": form, "posting": None})


@login_required
def roommate_edit(request, pk):
    posting = get_object_or_404(RoommatePosting, pk=pk, poster=request.user)
    if request.method == 'POST':
        form = RoommatePostingForm(request.POST, request.FILES, instance=posting)
        if form.is_valid():
            form.save()
            return redirect('roommates:detail', pk=posting.pk)
    else:
        form = RoommatePostingForm(instance=posting)
    return render(request, "roommates/form.html", {"form": form, "posting": posting})


@login_required
@require_POST
def roommate_toggle_active(request, pk):
    posting = get_object_or_404(RoommatePosting, pk=pk, poster=request.user)
    posting.is_active = not posting.is_active
    posting.save(update_fields=['is_active'])
    return redirect('roommates:detail', pk=posting.pk)


@login_required
@require_POST
def roommate_delete(request, pk):
    posting = get_object_or_404(RoommatePosting, pk=pk, poster=request.user)
    posting.delete()
    messages.success(request, 'Your roommate posting has been deleted.')
    return redirect('roommates:list')
