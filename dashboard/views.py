from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import TenantProfile, User
from cms.forms import FAQForm
from cms.models import FAQ
from inquiries.models import Inquiry
from notifications.models import Notification, notify
from properties.models import Property
from properties.views import _property_card_context, _saved_ids_for
from subscriptions.forms import SubscriptionPlanForm
from subscriptions.models import Payment, Subscription, SubscriptionPlan
from visits.models import Visit
from .decorators import admin_required, owner_or_hotel_required, super_admin_required, tenant_required
from .forms import (
    AccountBasicsForm, AdminCreateForm, LanguageForm, NotificationPreferencesForm,
    PrivacyPreferencesForm, SupportTicketForm, TenantProfileForm,
)
from .models import AuditLog, SupportTicket, log_admin_action

OWNER_COMING_SOON_SECTIONS = {
    'settings': (
        'Settings',
        'Notification, privacy and language preferences are coming in a future update. You can already update '
        'your name, phone number and password from My Profile.',
    ),
    'help': (
        'Help & Support',
        "A dedicated support ticket system for owners is coming in a future update. In the meantime, reach us "
        "from the Contact page.",
    ),
}

def _get_profile(user):
    profile, _ = TenantProfile.objects.get_or_create(user=user)
    return profile


@tenant_required
def tenant_home(request):
    tenant_profile = _get_profile(request.user)
    saved_ids = _saved_ids_for(request.user)

    recently_viewed_ids = request.session.get('recently_viewed_property_ids', [])
    viewed_qs = Property.objects.filter(pk__in=recently_viewed_ids, status=Property.Status.PUBLISHED).prefetch_related('photos', 'amenities')
    viewed_by_id = {p.pk: p for p in viewed_qs}
    recently_viewed = [
        _property_card_context(viewed_by_id[pid], saved_ids)
        for pid in recently_viewed_ids if pid in viewed_by_id
    ][:3]

    recommended_qs = Property.objects.filter(status=Property.Status.PUBLISHED).exclude(pk__in=saved_ids)
    if tenant_profile.preferred_city:
        recommended_qs = recommended_qs.filter(city__iexact=tenant_profile.preferred_city)
    recommended = [
        _property_card_context(p, saved_ids)
        for p in recommended_qs.prefetch_related('photos', 'amenities').order_by('-created_at')[:3]
    ]

    upcoming_visits = request.user.visits.filter(
        status__in=[Visit.Status.PENDING, Visit.Status.SCHEDULED], scheduled_at__gte=timezone.now(),
    ).select_related('property').order_by('scheduled_at')[:3]

    context = {
        'tenant_profile': tenant_profile,
        'saved_count': len(saved_ids),
        'active_inquiries_count': request.user.inquiries.filter(status=Inquiry.Status.OPEN).count(),
        'scheduled_visits_count': request.user.visits.filter(
            status__in=[Visit.Status.PENDING, Visit.Status.SCHEDULED],
        ).count(),
        'unread_notifications_count': request.user.notifications.filter(is_read=False).count(),
        'recently_viewed': recently_viewed,
        'recommended': recommended,
        'upcoming_visits': upcoming_visits,
        'latest_notifications': request.user.notifications.all()[:5],
    }
    return render(request, 'dashboard/home.html', context)


@tenant_required
def saved_properties(request):
    saved = request.user.saved_properties.select_related('property').prefetch_related('property__photos', 'property__amenities')
    saved_ids = {sp.property_id for sp in saved}
    properties = [_property_card_context(sp.property, saved_ids) for sp in saved]
    return render(request, 'dashboard/saved_properties.html', {'properties': properties})


@tenant_required
def profile(request):
    tenant_profile = _get_profile(request.user)
    if request.method == 'POST':
        account_form = AccountBasicsForm(request.POST, instance=request.user)
        profile_form = TenantProfileForm(request.POST, request.FILES, instance=tenant_profile)
        if account_form.is_valid() and profile_form.is_valid():
            account_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated.')
            return redirect('dashboard:tenant_profile')
    else:
        account_form = AccountBasicsForm(instance=request.user)
        profile_form = TenantProfileForm(instance=tenant_profile)

    return render(request, 'dashboard/profile.html', {
        'account_form': account_form,
        'profile_form': profile_form,
        'tenant_profile': tenant_profile,
    })


@tenant_required
def settings_home(request):
    tenant_profile = _get_profile(request.user)
    return render(request, 'dashboard/settings.html', {
        'tenant_profile': tenant_profile,
        'notification_form': NotificationPreferencesForm(instance=tenant_profile),
        'privacy_form': PrivacyPreferencesForm(instance=tenant_profile),
        'language_form': LanguageForm(instance=tenant_profile),
        'password_form': PasswordChangeForm(user=request.user),
    })


@tenant_required
@require_POST
def settings_password(request):
    form = PasswordChangeForm(user=request.user, data=request.POST)
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, 'Password changed.')
    else:
        messages.error(request, ' '.join(e for errs in form.errors.values() for e in errs))
    return redirect('dashboard:tenant_settings')


@tenant_required
@require_POST
def settings_notifications(request):
    form = NotificationPreferencesForm(request.POST, instance=_get_profile(request.user))
    if form.is_valid():
        form.save()
        messages.success(request, 'Notification preferences updated.')
    return redirect('dashboard:tenant_settings')


@tenant_required
@require_POST
def settings_privacy(request):
    form = PrivacyPreferencesForm(request.POST, instance=_get_profile(request.user))
    if form.is_valid():
        form.save()
        messages.success(request, 'Privacy settings updated.')
    return redirect('dashboard:tenant_settings')


@tenant_required
@require_POST
def settings_language(request):
    form = LanguageForm(request.POST, instance=_get_profile(request.user))
    if form.is_valid():
        form.save()
        messages.success(request, 'Language preference updated.')
    return redirect('dashboard:tenant_settings')


@tenant_required
@require_POST
def settings_delete_account(request):
    if request.POST.get('confirm', '').strip().upper() != 'DELETE':
        messages.error(request, 'Type DELETE to confirm account deactivation.')
        return redirect('dashboard:tenant_settings')
    user = request.user
    user.is_active = False
    user.save(update_fields=['is_active'])
    auth_logout(request)
    messages.success(request, 'Your account has been deactivated.')
    return redirect('accounts:login')


@tenant_required
def help_support(request):
    if request.method == 'POST':
        form = SupportTicketForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.save()
            Notification.objects.create(
                user=request.user, message=f'Your support ticket "{ticket.subject}" has been submitted.',
                category=Notification.Category.TICKET, url='/tenant/dashboard/help/',
            )
            messages.success(request, "Ticket submitted — our support team will get back to you by email.")
            return redirect('dashboard:tenant_help')
    else:
        form = SupportTicketForm()

    faqs = FAQ.objects.filter(placement=FAQ.Placement.TENANT_HELP, is_published=True)
    return render(request, 'dashboard/help_support.html', {'form': form, 'faqs': faqs})


@owner_or_hotel_required
def owner_home(request):
    properties = request.user.properties.all()
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    hour = now.hour
    greeting = 'Good morning' if hour < 12 else 'Good afternoon' if hour < 17 else 'Good evening'

    open_inquiries = Inquiry.objects.filter(property__owner=request.user, status=Inquiry.Status.OPEN)
    stats = {
        'total_listings': properties.count(),
        'active_listings': properties.filter(status=Property.Status.PUBLISHED).count(),
        'draft_listings': properties.filter(status=Property.Status.DRAFT).count(),
        'new_inquiries': open_inquiries.count(),
        'scheduled_visits': Visit.objects.filter(
            property__owner=request.user, status__in=[Visit.Status.PENDING, Visit.Status.SCHEDULED],
            scheduled_at__gte=now,
        ).count(),
        'added_this_month': properties.filter(created_at__gte=month_start).count(),
    }

    context = {
        'greeting': greeting,
        'stats': stats,
        'recent_properties': properties.prefetch_related('photos').annotate(
            inquiries_count=Count('inquiries', distinct=True),
        )[:5],
        'recent_inquiries': Inquiry.objects.filter(property__owner=request.user)
            .select_related('property', 'tenant')[:5],
        'upcoming_visits': Visit.objects.filter(
            property__owner=request.user, status__in=[Visit.Status.PENDING, Visit.Status.SCHEDULED],
            scheduled_at__gte=now,
        ).select_related('property', 'tenant').order_by('scheduled_at')[:5],
    }
    return render(request, 'dashboard/owner_home.html', context)


@owner_or_hotel_required
def owner_profile(request):
    if request.method == 'POST':
        account_form = AccountBasicsForm(request.POST, instance=request.user)
        if account_form.is_valid():
            account_form.save()
            messages.success(request, 'Profile updated.')
            return redirect('dashboard:owner_profile')
    else:
        account_form = AccountBasicsForm(instance=request.user)

    return render(request, 'dashboard/owner_profile.html', {
        'account_form': account_form,
        'password_form': PasswordChangeForm(user=request.user),
    })


@owner_or_hotel_required
@require_POST
def owner_profile_password(request):
    form = PasswordChangeForm(user=request.user, data=request.POST)
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, 'Password changed.')
    else:
        messages.error(request, ' '.join(e for errs in form.errors.values() for e in errs))
    return redirect('dashboard:owner_profile')


@owner_or_hotel_required
def owner_inquiries(request):
    all_inquiries = Inquiry.objects.filter(property__owner=request.user).select_related('tenant', 'property')
    stats = {
        'total': all_inquiries.count(),
        'open': all_inquiries.filter(status=Inquiry.Status.OPEN).count(),
        'closed': all_inquiries.filter(status=Inquiry.Status.CLOSED).count(),
    }

    queryset = all_inquiries
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    if q:
        queryset = queryset.filter(Q(tenant__full_name__icontains=q) | Q(property__title__icontains=q))
    if status:
        queryset = queryset.filter(status=status)

    paginator = Paginator(queryset.order_by('-created_at'), 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    carry_params = request.GET.copy()
    carry_params.pop('page', None)

    return render(request, 'dashboard/owner_inquiries.html', {
        'inquiries': page_obj,
        'page_obj': page_obj,
        'carry_qs': carry_params.urlencode(),
        'stats': stats,
        'status_options': Inquiry.Status.choices,
        'selected_q': q,
        'selected_status': status,
    })


@owner_or_hotel_required
@require_POST
def owner_inquiry_set_status(request, pk, status):
    inquiry = get_object_or_404(Inquiry, pk=pk, property__owner=request.user)
    allowed = {Inquiry.Status.OPEN, Inquiry.Status.CLOSED}
    if status not in allowed:
        raise Http404('Invalid status change.')
    inquiry.status = status
    inquiry.save(update_fields=['status'])
    messages.success(request, f'Inquiry marked as {inquiry.get_status_display()}.')
    return redirect('dashboard:owner_inquiries')


@owner_or_hotel_required
def owner_visits(request):
    all_visits = Visit.objects.filter(property__owner=request.user).select_related('tenant', 'property')
    stats = {
        'total': all_visits.count(),
        'pending': all_visits.filter(status=Visit.Status.PENDING).count(),
        'scheduled': all_visits.filter(status=Visit.Status.SCHEDULED).count(),
        'completed': all_visits.filter(status=Visit.Status.COMPLETED).count(),
        'cancelled': all_visits.filter(status=Visit.Status.CANCELLED).count(),
    }

    queryset = all_visits
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    if q:
        queryset = queryset.filter(Q(tenant__full_name__icontains=q) | Q(property__title__icontains=q))
    if status:
        queryset = queryset.filter(status=status)

    paginator = Paginator(queryset.order_by('-scheduled_at'), 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    carry_params = request.GET.copy()
    carry_params.pop('page', None)

    return render(request, 'dashboard/owner_visits.html', {
        'visits': page_obj,
        'page_obj': page_obj,
        'carry_qs': carry_params.urlencode(),
        'stats': stats,
        'status_options': Visit.Status.choices,
        'selected_q': q,
        'selected_status': status,
    })


@owner_or_hotel_required
@require_POST
def owner_visit_cancel(request, pk):
    visit = get_object_or_404(Visit, pk=pk, property__owner=request.user)
    if visit.status == Visit.Status.SCHEDULED:
        visit.status = Visit.Status.CANCELLED
        visit.save(update_fields=['status'])
        notify(
            visit.tenant, f'Your visit for "{visit.property.title or "a property"}" was cancelled by the owner.',
            category=Notification.Category.VISIT, url='/tenant/dashboard/visits/',
        )
        messages.success(request, 'Visit cancelled.')
    return redirect('dashboard:owner_visits')


@owner_or_hotel_required
@require_POST
def owner_visit_approve(request, pk):
    visit = get_object_or_404(Visit, pk=pk, property__owner=request.user)
    if visit.status == Visit.Status.PENDING:
        visit.status = Visit.Status.SCHEDULED
        visit.save(update_fields=['status'])
        notify(
            visit.tenant,
            f'Your visit for "{visit.property.title or "a property"}" on {visit.scheduled_at:%d %b %Y, %I:%M %p} was confirmed by the owner.',
            category=Notification.Category.VISIT, url='/tenant/dashboard/visits/',
        )
        messages.success(request, 'Visit approved.')
    return redirect('dashboard:owner_visits')


@owner_or_hotel_required
@require_POST
def owner_visit_decline(request, pk):
    visit = get_object_or_404(Visit, pk=pk, property__owner=request.user)
    if visit.status == Visit.Status.PENDING:
        visit.status = Visit.Status.CANCELLED
        visit.save(update_fields=['status'])
        notify(
            visit.tenant, f'Your visit request for "{visit.property.title or "a property"}" was declined by the owner.',
            category=Notification.Category.VISIT, url='/tenant/dashboard/visits/',
        )
        messages.success(request, 'Visit declined.')
    return redirect('dashboard:owner_visits')


@owner_or_hotel_required
def owner_coming_soon(request, section):
    if section not in OWNER_COMING_SOON_SECTIONS:
        raise Http404('Unknown dashboard section.')
    title, description = OWNER_COMING_SOON_SECTIONS[section]
    return render(request, 'dashboard/owner_coming_soon.html', {'title': title, 'description': description})


def _month_start():
    now = timezone.now()
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


@admin_required
def admin_home(request):
    users_qs = User.objects.filter(role__in=User.PUBLIC_ROLES)
    now = timezone.now()
    stats = {
        'total_users': users_qs.count(),
        'active_users': users_qs.filter(is_active=True).count(),
        'new_users_this_month': users_qs.filter(date_joined__gte=_month_start()).count(),
        'blocked_users': users_qs.filter(is_active=False).count(),
        'total_properties': Property.objects.count(),
        'active_properties': Property.objects.filter(status=Property.Status.PUBLISHED).count(),
        'draft_properties': Property.objects.filter(status=Property.Status.DRAFT).count(),
        'total_inquiries': Inquiry.objects.count(),
        'scheduled_visits': Visit.objects.filter(
            status__in=[Visit.Status.PENDING, Visit.Status.SCHEDULED], scheduled_at__gte=now,
        ).count(),
        'open_tickets': SupportTicket.objects.filter(status=SupportTicket.Status.OPEN).count(),
    }

    activity = []
    for u in users_qs.order_by('-date_joined')[:5]:
        activity.append({
            'icon': 'user', 'at': u.date_joined,
            'text': f'{u.full_name} registered as {u.get_role_display()}',
        })
    for p in Property.objects.select_related('owner').order_by('-created_at')[:5]:
        activity.append({
            'icon': 'building', 'at': p.created_at,
            'text': f'{p.owner.full_name} listed "{p.title or "a draft property"}"',
        })
    for i in Inquiry.objects.select_related('tenant', 'property').order_by('-created_at')[:5]:
        activity.append({
            'icon': 'chat', 'at': i.created_at,
            'text': f'{i.tenant.full_name} inquired about "{i.property.title or "a property"}"',
        })
    for t in SupportTicket.objects.select_related('user').order_by('-created_at')[:5]:
        activity.append({
            'icon': 'headset', 'at': t.created_at,
            'text': f'{t.user.full_name} submitted a support ticket: "{t.subject}"',
        })
    activity.sort(key=lambda item: item['at'], reverse=True)

    return render(request, 'dashboard/admin_home.html', {
        'stats': stats,
        'recent_activity': activity[:8],
    })


@admin_required
def admin_users(request):
    all_users = User.objects.filter(role__in=User.PUBLIC_ROLES)
    stats = {
        'total': all_users.count(),
        'active': all_users.filter(is_active=True).count(),
        'new_this_month': all_users.filter(date_joined__gte=_month_start()).count(),
        'blocked': all_users.filter(is_active=False).count(),
    }

    queryset = all_users.annotate(
        properties_count=Count('properties', distinct=True),
        inquiries_count=Count('inquiries', distinct=True),
    )

    q = request.GET.get('q', '').strip()
    role = request.GET.get('role', '')
    status = request.GET.get('status', '')

    if q:
        queryset = queryset.filter(Q(full_name__icontains=q) | Q(email__icontains=q) | Q(mobile_number__icontains=q))
    if role:
        queryset = queryset.filter(role=role)
    if status == 'active':
        queryset = queryset.filter(is_active=True)
    elif status == 'blocked':
        queryset = queryset.filter(is_active=False)

    paginator = Paginator(queryset.order_by('-date_joined'), 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    carry_params = request.GET.copy()
    carry_params.pop('page', None)

    return render(request, 'dashboard/admin_users.html', {
        'users_page': page_obj,
        'page_obj': page_obj,
        'carry_qs': carry_params.urlencode(),
        'stats': stats,
        'role_options': [(r, User.Role(r).label) for r in User.PUBLIC_ROLES],
        'selected_q': q,
        'selected_role': role,
        'selected_status': status,
    })


@admin_required
@require_POST
def admin_user_set_active(request, pk, active):
    target = get_object_or_404(User, pk=pk, role__in=User.PUBLIC_ROLES)
    target.is_active = active
    target.save(update_fields=['is_active'])
    action = 'Unblocked' if active else 'Blocked'
    log_admin_action(
        request.user, f'{action} user {target.full_name} ({target.email})',
        target_type='User', target_id=target.pk, target_repr=target.full_name,
    )
    messages.success(request, f'{target.full_name} has been {"unblocked" if active else "blocked"}.')
    return redirect('dashboard:admin_users')


@admin_required
def admin_profile(request):
    if request.method == 'POST':
        account_form = AccountBasicsForm(request.POST, instance=request.user)
        if account_form.is_valid():
            account_form.save()
            messages.success(request, 'Profile updated.')
            return redirect('dashboard:admin_profile')
    else:
        account_form = AccountBasicsForm(instance=request.user)

    return render(request, 'dashboard/admin_profile.html', {
        'account_form': account_form,
        'password_form': PasswordChangeForm(user=request.user),
    })


@admin_required
@require_POST
def admin_profile_password(request):
    form = PasswordChangeForm(user=request.user, data=request.POST)
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, 'Password changed.')
    else:
        messages.error(request, ' '.join(e for errs in form.errors.values() for e in errs))
    return redirect('dashboard:admin_profile')


@super_admin_required
def admin_settings_stub(request):
    return render(request, 'dashboard/owner_coming_soon.html', {
        'title': 'Settings',
        'description': 'Platform-wide configuration settings are coming in a future update. You can already '
                        'update your name, phone number and password from My Profile.',
    })


@admin_required
def admin_properties(request):
    all_properties = Property.objects.all()
    stats = {
        'total': all_properties.count(),
        'active': all_properties.filter(status=Property.Status.PUBLISHED).count(),
        'pending_review': all_properties.filter(
            status=Property.Status.PUBLISHED, verified_at__isnull=True, rejection_reason='',
        ).count(),
        'rejected': all_properties.exclude(rejection_reason='').count(),
        'draft': all_properties.filter(status=Property.Status.DRAFT).count(),
    }

    queryset = all_properties.select_related('owner').prefetch_related('photos').annotate(
        inquiries_count=Count('inquiries', distinct=True),
    )

    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    verification = request.GET.get('verification', '')
    property_type = request.GET.get('property_type', '')

    if q:
        queryset = queryset.filter(
            Q(title__icontains=q) | Q(city__icontains=q)
            | Q(owner__full_name__icontains=q) | Q(owner__email__icontains=q)
        )
    if status:
        queryset = queryset.filter(status=status)
    if verification == 'pending':
        queryset = queryset.filter(status=Property.Status.PUBLISHED, verified_at__isnull=True, rejection_reason='')
    elif verification == 'verified':
        queryset = queryset.filter(verified_at__isnull=False)
    elif verification == 'rejected':
        queryset = queryset.exclude(rejection_reason='')
    if property_type:
        queryset = queryset.filter(property_type=property_type)

    paginator = Paginator(queryset.order_by('-created_at'), 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    carry_params = request.GET.copy()
    carry_params.pop('page', None)

    return render(request, 'dashboard/admin_properties.html', {
        'properties': page_obj,
        'page_obj': page_obj,
        'carry_qs': carry_params.urlencode(),
        'stats': stats,
        'status_options': Property.Status.choices,
        'property_type_options': Property.PropertyType.choices,
        'selected_q': q,
        'selected_status': status,
        'selected_verification': verification,
        'selected_property_type': property_type,
    })


@admin_required
def admin_property_detail(request, pk):
    property_obj = get_object_or_404(Property.objects.select_related('owner', 'verified_by'), pk=pk)
    checklist = [
        (label, bool(getattr(property_obj, field)))
        for field, label in Property.REQUIRED_FOR_PUBLISH
    ]
    checklist.append((
        f'At least {Property.MIN_PHOTOS_TO_PUBLISH} photos (currently {property_obj.photos.count()})',
        property_obj.photos.count() >= Property.MIN_PHOTOS_TO_PUBLISH,
    ))
    return render(request, 'dashboard/admin_property_detail.html', {
        'property': property_obj,
        'checklist': checklist,
    })


@admin_required
@require_POST
def admin_property_approve(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)
    property_obj.verified_at = timezone.now()
    property_obj.verified_by = request.user
    property_obj.rejection_reason = ''
    property_obj.save(update_fields=['verified_at', 'verified_by', 'rejection_reason'])
    notify(
        property_obj.owner, f'Your listing "{property_obj.title or "Untitled draft"}" has been reviewed and verified.',
        category=Notification.Category.SYSTEM, url='/properties/manage/',
    )
    log_admin_action(
        request.user, f'Approved property "{property_obj.title or "Untitled draft"}"',
        target_type='Property', target_id=property_obj.pk, target_repr=property_obj.title or 'Untitled draft',
    )
    messages.success(request, 'Listing marked as verified.')
    return redirect('dashboard:admin_property_detail', pk=pk)


@admin_required
def admin_property_reject(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)
    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        if not reason:
            messages.error(request, 'A reason is required to reject a listing.')
            return render(request, 'dashboard/admin_property_reject.html', {'property': property_obj, 'reason': reason})
        property_obj.status = Property.Status.DRAFT
        property_obj.rejection_reason = reason
        property_obj.verified_at = None
        property_obj.verified_by = None
        property_obj.save(update_fields=['status', 'rejection_reason', 'verified_at', 'verified_by'])
        notify(
            property_obj.owner,
            f'Your listing "{property_obj.title or "Untitled draft"}" was rejected: {reason}',
            category=Notification.Category.SYSTEM, url='/properties/manage/',
        )
        log_admin_action(
            request.user, f'Rejected property "{property_obj.title or "Untitled draft"}": {reason}',
            target_type='Property', target_id=property_obj.pk, target_repr=property_obj.title or 'Untitled draft',
        )
        messages.success(request, 'Listing rejected and returned to draft.')
        return redirect('dashboard:admin_properties')

    return render(request, 'dashboard/admin_property_reject.html', {'property': property_obj, 'reason': ''})


@admin_required
@require_POST
def admin_property_set_status(request, pk, status):
    property_obj = get_object_or_404(Property, pk=pk)
    allowed = {Property.Status.PUBLISHED, Property.Status.PAUSED, Property.Status.ARCHIVED}
    if status not in allowed:
        raise Http404('Invalid status change.')
    property_obj.status = status
    update_fields = ['status']
    if status == Property.Status.PUBLISHED:
        if not property_obj.published_at:
            property_obj.published_at = timezone.now()
            update_fields.append('published_at')
        property_obj.rejection_reason = ''
        update_fields.append('rejection_reason')
    property_obj.save(update_fields=update_fields)
    if status == Property.Status.ARCHIVED:
        notify(
            property_obj.owner, f'Your listing "{property_obj.title or "Untitled draft"}" was archived by an admin.',
            category=Notification.Category.SYSTEM, url='/properties/manage/',
        )
    log_admin_action(
        request.user, f'Marked property "{property_obj.title or "Untitled draft"}" as {property_obj.get_status_display()}',
        target_type='Property', target_id=property_obj.pk, target_repr=property_obj.title or 'Untitled draft',
    )
    messages.success(request, f'Listing marked as {property_obj.get_status_display()}.')
    return redirect('dashboard:admin_properties')


@admin_required
def admin_inquiries(request):
    all_inquiries = Inquiry.objects.select_related('tenant', 'property', 'property__owner')
    stats = {
        'total': all_inquiries.count(),
        'open': all_inquiries.filter(status=Inquiry.Status.OPEN).count(),
        'closed': all_inquiries.filter(status=Inquiry.Status.CLOSED).count(),
    }

    queryset = all_inquiries
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    if q:
        queryset = queryset.filter(
            Q(tenant__full_name__icontains=q) | Q(property__title__icontains=q)
            | Q(property__owner__full_name__icontains=q)
        )
    if status:
        queryset = queryset.filter(status=status)

    paginator = Paginator(queryset.order_by('-created_at'), 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    carry_params = request.GET.copy()
    carry_params.pop('page', None)

    return render(request, 'dashboard/admin_inquiries.html', {
        'inquiries': page_obj,
        'page_obj': page_obj,
        'carry_qs': carry_params.urlencode(),
        'stats': stats,
        'status_options': Inquiry.Status.choices,
        'selected_q': q,
        'selected_status': status,
    })


@admin_required
@require_POST
def admin_inquiry_set_status(request, pk, status):
    inquiry = get_object_or_404(Inquiry, pk=pk)
    allowed = {Inquiry.Status.OPEN, Inquiry.Status.CLOSED}
    if status not in allowed:
        raise Http404('Invalid status change.')
    inquiry.status = status
    inquiry.save(update_fields=['status'])
    log_admin_action(
        request.user, f'Marked inquiry from {inquiry.tenant.full_name} as {inquiry.get_status_display()}',
        target_type='Inquiry', target_id=inquiry.pk, target_repr=f'{inquiry.tenant.full_name} → {inquiry.property}',
    )
    messages.success(request, f'Inquiry marked as {inquiry.get_status_display()}.')
    return redirect('dashboard:admin_inquiries')


@admin_required
def admin_visits(request):
    all_visits = Visit.objects.select_related('tenant', 'property', 'property__owner')
    stats = {
        'total': all_visits.count(),
        'pending': all_visits.filter(status=Visit.Status.PENDING).count(),
        'scheduled': all_visits.filter(status=Visit.Status.SCHEDULED).count(),
        'completed': all_visits.filter(status=Visit.Status.COMPLETED).count(),
        'cancelled': all_visits.filter(status=Visit.Status.CANCELLED).count(),
    }

    queryset = all_visits
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    if q:
        queryset = queryset.filter(
            Q(tenant__full_name__icontains=q) | Q(property__title__icontains=q)
            | Q(property__owner__full_name__icontains=q)
        )
    if status:
        queryset = queryset.filter(status=status)

    paginator = Paginator(queryset.order_by('-scheduled_at'), 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    carry_params = request.GET.copy()
    carry_params.pop('page', None)

    return render(request, 'dashboard/admin_visits.html', {
        'visits': page_obj,
        'page_obj': page_obj,
        'carry_qs': carry_params.urlencode(),
        'stats': stats,
        'status_options': Visit.Status.choices,
        'selected_q': q,
        'selected_status': status,
    })


@admin_required
@require_POST
def admin_visit_cancel(request, pk):
    visit = get_object_or_404(Visit, pk=pk)
    visit.status = Visit.Status.CANCELLED
    visit.save(update_fields=['status'])
    notify(
        visit.tenant, f'Your visit for "{visit.property.title or "a property"}" was cancelled by an admin.',
        category=Notification.Category.VISIT, url='/tenant/dashboard/visits/',
    )
    log_admin_action(
        request.user, f'Cancelled visit for {visit.tenant.full_name} at "{visit.property}"',
        target_type='Visit', target_id=visit.pk, target_repr=f'{visit.tenant.full_name} → {visit.property}',
    )
    messages.success(request, 'Visit cancelled.')
    return redirect('dashboard:admin_visits')


@admin_required
def admin_support(request):
    all_tickets = SupportTicket.objects.select_related('user')
    stats = {
        'total': all_tickets.count(),
        'open': all_tickets.filter(status=SupportTicket.Status.OPEN).count(),
        'resolved': all_tickets.filter(status=SupportTicket.Status.RESOLVED).count(),
    }

    queryset = all_tickets
    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    status = request.GET.get('status', '')
    if q:
        queryset = queryset.filter(
            Q(subject__icontains=q) | Q(user__full_name__icontains=q) | Q(user__email__icontains=q)
        )
    if category:
        queryset = queryset.filter(category=category)
    if status:
        queryset = queryset.filter(status=status)

    paginator = Paginator(queryset.order_by('-created_at'), 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    carry_params = request.GET.copy()
    carry_params.pop('page', None)

    return render(request, 'dashboard/admin_support.html', {
        'tickets': page_obj,
        'page_obj': page_obj,
        'carry_qs': carry_params.urlencode(),
        'stats': stats,
        'category_options': SupportTicket.Category.choices,
        'status_options': SupportTicket.Status.choices,
        'selected_q': q,
        'selected_category': category,
        'selected_status': status,
    })


@admin_required
@require_POST
def admin_support_set_status(request, pk, status):
    ticket = get_object_or_404(SupportTicket, pk=pk)
    allowed = {SupportTicket.Status.OPEN, SupportTicket.Status.RESOLVED}
    if status not in allowed:
        raise Http404('Invalid status change.')
    ticket.status = status
    ticket.save(update_fields=['status'])
    notify(
        ticket.user, f'Your support ticket "{ticket.subject}" was marked {ticket.get_status_display().lower()}.',
        category=Notification.Category.TICKET,
    )
    log_admin_action(
        request.user, f'Marked support ticket "{ticket.subject}" as {ticket.get_status_display()}',
        target_type='SupportTicket', target_id=ticket.pk, target_repr=ticket.subject,
    )
    messages.success(request, f'Ticket marked as {ticket.get_status_display()}.')
    return redirect('dashboard:admin_support')


def _weekly_buckets(queryset, date_field, weeks=8):
    """Real, zero-filled weekly counts for the last `weeks` Monday-aligned
    weeks — used for the Reports charts. No external charting library;
    templates render these as plain CSS bar charts."""
    today = timezone.now().date()
    this_monday = today - timedelta(days=today.weekday())
    buckets = []
    for i in range(weeks - 1, -1, -1):
        start = this_monday - timedelta(weeks=i)
        end = start + timedelta(days=7)
        count = queryset.filter(**{
            f'{date_field}__date__gte': start,
            f'{date_field}__date__lt': end,
        }).count()
        buckets.append({'label': start.strftime('%d %b'), 'count': count})
    max_count = max((b['count'] for b in buckets), default=0) or 1
    for b in buckets:
        b['pct'] = round(b['count'] / max_count * 100)
    return buckets


@admin_required
def admin_reports(request):
    users_qs = User.objects.filter(role__in=User.PUBLIC_ROLES)
    stats = {
        'total_users': users_qs.count(),
        'total_properties': Property.objects.count(),
        'total_inquiries': Inquiry.objects.count(),
        'total_visits': Visit.objects.count(),
    }

    user_growth = _weekly_buckets(users_qs, 'date_joined')
    inquiry_trend = _weekly_buckets(Inquiry.objects.all(), 'created_at')

    property_status_breakdown = []
    reserved = (Property.Status.PENDING_VERIFICATION, Property.Status.PENDING_REVIEW)
    for value, label in Property.Status.choices:
        if value in reserved:
            continue
        count = Property.objects.filter(status=value).count()
        property_status_breakdown.append({'label': label, 'count': count})
    breakdown_total = sum(item['count'] for item in property_status_breakdown) or 1
    for item in property_status_breakdown:
        item['pct'] = round(item['count'] / breakdown_total * 100)

    top_cities_qs = Property.objects.exclude(city='').values('city').annotate(count=Count('id')).order_by('-count')[:5]
    max_city_count = max((c['count'] for c in top_cities_qs), default=0) or 1
    top_cities = [
        {'city': c['city'], 'count': c['count'], 'pct': round(c['count'] / max_city_count * 100)}
        for c in top_cities_qs
    ]

    return render(request, 'dashboard/admin_reports.html', {
        'stats': stats,
        'user_growth': user_growth,
        'inquiry_trend': inquiry_trend,
        'property_status_breakdown': property_status_breakdown,
        'top_cities': top_cities,
    })


@admin_required
def admin_audit_logs(request):
    all_logs = AuditLog.objects.select_related('admin')
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    stats = {
        'total': all_logs.count(),
        'today': all_logs.filter(created_at__date=today).count(),
        'this_week': all_logs.filter(created_at__date__gte=week_start).count(),
    }

    queryset = all_logs
    q = request.GET.get('q', '').strip()
    target_type = request.GET.get('target_type', '')
    if q:
        queryset = queryset.filter(Q(message__icontains=q) | Q(admin__full_name__icontains=q))
    if target_type:
        queryset = queryset.filter(target_type=target_type)

    paginator = Paginator(queryset.order_by('-created_at'), 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    carry_params = request.GET.copy()
    carry_params.pop('page', None)

    target_type_options = (
        AuditLog.objects.exclude(target_type='').values_list('target_type', flat=True).distinct().order_by('target_type')
    )

    return render(request, 'dashboard/admin_audit_logs.html', {
        'logs': page_obj,
        'page_obj': page_obj,
        'carry_qs': carry_params.urlencode(),
        'stats': stats,
        'target_type_options': target_type_options,
        'selected_q': q,
        'selected_target_type': target_type,
    })


@admin_required
def admin_cms_faqs(request):
    all_faqs = FAQ.objects.all()
    stats = {
        'total': all_faqs.count(),
        'published': all_faqs.filter(is_published=True).count(),
        'contact': all_faqs.filter(placement=FAQ.Placement.CONTACT).count(),
        'tenant_help': all_faqs.filter(placement=FAQ.Placement.TENANT_HELP).count(),
    }

    queryset = all_faqs
    q = request.GET.get('q', '').strip()
    placement = request.GET.get('placement', '')
    if q:
        queryset = queryset.filter(Q(question__icontains=q) | Q(answer__icontains=q))
    if placement:
        queryset = queryset.filter(placement=placement)

    paginator = Paginator(queryset, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    carry_params = request.GET.copy()
    carry_params.pop('page', None)

    return render(request, 'dashboard/admin_cms_faqs.html', {
        'faqs': page_obj,
        'page_obj': page_obj,
        'carry_qs': carry_params.urlencode(),
        'stats': stats,
        'placement_options': FAQ.Placement.choices,
        'selected_q': q,
        'selected_placement': placement,
    })


@admin_required
def admin_cms_faq_form(request, pk=None):
    faq = get_object_or_404(FAQ, pk=pk) if pk else None
    if request.method == 'POST':
        form = FAQForm(request.POST, instance=faq)
        if form.is_valid():
            is_new = faq is None
            faq = form.save()
            log_admin_action(
                request.user, f'{"Created" if is_new else "Updated"} FAQ "{faq.question}"',
                target_type='FAQ', target_id=faq.pk, target_repr=faq.question,
            )
            messages.success(request, f'FAQ {"created" if is_new else "updated"}.')
            return redirect('dashboard:admin_cms')
    else:
        form = FAQForm(instance=faq)

    return render(request, 'dashboard/admin_cms_faq_form.html', {'form': form, 'faq': faq})


@admin_required
@require_POST
def admin_cms_faq_delete(request, pk):
    faq = get_object_or_404(FAQ, pk=pk)
    question = faq.question
    faq.delete()
    log_admin_action(request.user, f'Deleted FAQ "{question}"', target_type='FAQ', target_repr=question)
    messages.success(request, 'FAQ deleted.')
    return redirect('dashboard:admin_cms')


@admin_required
@require_POST
def admin_cms_faq_toggle(request, pk):
    faq = get_object_or_404(FAQ, pk=pk)
    faq.is_published = not faq.is_published
    faq.save(update_fields=['is_published'])
    log_admin_action(
        request.user, f'{"Published" if faq.is_published else "Unpublished"} FAQ "{faq.question}"',
        target_type='FAQ', target_id=faq.pk, target_repr=faq.question,
    )
    messages.success(request, f'FAQ {"published" if faq.is_published else "unpublished"}.')
    return redirect('dashboard:admin_cms')


@admin_required
def admin_subscriptions(request):
    plans = SubscriptionPlan.objects.all()
    stats = {
        'total': plans.count(),
        'active': plans.filter(is_active=True).count(),
        'active_subscribers': Subscription.objects.filter(
            status=Subscription.Status.ACTIVE, current_period_end__gt=timezone.now(),
        ).count(),
    }
    return render(request, 'dashboard/admin_subscriptions.html', {'plans': plans, 'stats': stats})


@admin_required
def admin_subscription_plan_form(request, pk=None):
    plan = get_object_or_404(SubscriptionPlan, pk=pk) if pk else None
    if request.method == 'POST':
        form = SubscriptionPlanForm(request.POST, instance=plan)
        if form.is_valid():
            is_new = plan is None
            plan = form.save()
            log_admin_action(
                request.user, f'{"Created" if is_new else "Updated"} subscription plan "{plan.name}"',
                target_type='SubscriptionPlan', target_id=plan.pk, target_repr=plan.name,
            )
            messages.success(request, f'Plan {"created" if is_new else "updated"}.')
            return redirect('dashboard:admin_subscriptions')
    else:
        form = SubscriptionPlanForm(instance=plan)

    return render(request, 'dashboard/admin_subscription_plan_form.html', {'form': form, 'plan': plan})


@admin_required
@require_POST
def admin_subscription_plan_toggle(request, pk):
    plan = get_object_or_404(SubscriptionPlan, pk=pk)
    plan.is_active = not plan.is_active
    plan.save(update_fields=['is_active'])
    log_admin_action(
        request.user, f'{"Activated" if plan.is_active else "Deactivated"} subscription plan "{plan.name}"',
        target_type='SubscriptionPlan', target_id=plan.pk, target_repr=plan.name,
    )
    messages.success(request, f'Plan {"activated" if plan.is_active else "deactivated"}.')
    return redirect('dashboard:admin_subscriptions')


@admin_required
def admin_payments(request):
    all_payments = Payment.objects.select_related('owner', 'plan')
    stats = {
        'total': all_payments.count(),
        'paid': all_payments.filter(status=Payment.Status.PAID).count(),
        'failed': all_payments.filter(status=Payment.Status.FAILED).count(),
        'total_revenue': sum(
            (p.amount for p in all_payments.filter(status=Payment.Status.PAID)), start=0,
        ),
    }

    queryset = all_payments
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    if q:
        queryset = queryset.filter(
            Q(owner__full_name__icontains=q) | Q(owner__email__icontains=q) | Q(razorpay_order_id__icontains=q)
        )
    if status:
        queryset = queryset.filter(status=status)

    paginator = Paginator(queryset.order_by('-created_at'), 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    carry_params = request.GET.copy()
    carry_params.pop('page', None)

    return render(request, 'dashboard/admin_payments.html', {
        'payments': page_obj,
        'page_obj': page_obj,
        'carry_qs': carry_params.urlencode(),
        'stats': stats,
        'status_options': Payment.Status.choices,
        'selected_q': q,
        'selected_status': status,
    })


def _is_last_active_super_admin(user):
    if user.role != User.Role.SUPER_ADMIN:
        return False
    return not User.objects.filter(
        role=User.Role.SUPER_ADMIN, is_active=True,
    ).exclude(pk=user.pk).exists()


@super_admin_required
def admin_internal_users(request):
    """Manage other Admin/Super Admin accounts — separate from the
    public-facing User Management (Feature 06), which deliberately excludes
    internal roles. Super-Admin-only (Feature 13's simple RBAC)."""
    all_admins = User.objects.filter(role__in=User.INTERNAL_ROLES).order_by('-date_joined')
    stats = {
        'total': all_admins.count(),
        'active': all_admins.filter(is_active=True).count(),
        'super_admins': all_admins.filter(role=User.Role.SUPER_ADMIN).count(),
    }
    return render(request, 'dashboard/admin_internal_users.html', {
        'admins': all_admins, 'stats': stats, 'current_user_id': request.user.pk,
    })


@super_admin_required
def admin_user_create(request):
    if request.method == 'POST':
        form = AdminCreateForm(request.POST)
        if form.is_valid():
            new_admin = form.save()
            log_admin_action(
                request.user, f'Created {new_admin.get_role_display()} account for {new_admin.email}',
                target_type='User', target_id=new_admin.pk, target_repr=new_admin.email,
            )
            messages.success(request, f'{new_admin.get_role_display()} account created for {new_admin.email}.')
            return redirect('dashboard:admin_internal_users')
    else:
        form = AdminCreateForm()

    return render(request, 'dashboard/admin_user_create.html', {'form': form})


@super_admin_required
@require_POST
def admin_user_set_role(request, pk, role):
    target = get_object_or_404(User, pk=pk, role__in=User.INTERNAL_ROLES)
    if role not in (User.Role.ADMIN, User.Role.SUPER_ADMIN):
        raise Http404('Invalid role.')
    if target.pk == request.user.pk:
        messages.error(request, "You can't change your own role — ask another Super Admin.")
        return redirect('dashboard:admin_internal_users')
    if role == User.Role.ADMIN and _is_last_active_super_admin(target):
        messages.error(request, "Can't demote the last remaining active Super Admin.")
        return redirect('dashboard:admin_internal_users')

    target.role = role
    target.save(update_fields=['role'])
    log_admin_action(
        request.user, f'Changed {target.email} role to {target.get_role_display()}',
        target_type='User', target_id=target.pk, target_repr=target.email,
    )
    messages.success(request, f'{target.email} is now {target.get_role_display()}.')
    return redirect('dashboard:admin_internal_users')


@super_admin_required
@require_POST
def admin_user_set_active_internal(request, pk, active):
    target = get_object_or_404(User, pk=pk, role__in=User.INTERNAL_ROLES)
    if target.pk == request.user.pk:
        messages.error(request, "You can't deactivate your own account.")
        return redirect('dashboard:admin_internal_users')
    if not active and _is_last_active_super_admin(target):
        messages.error(request, "Can't deactivate the last remaining active Super Admin.")
        return redirect('dashboard:admin_internal_users')

    target.is_active = active
    target.save(update_fields=['is_active'])
    log_admin_action(
        request.user, f'{"Activated" if active else "Deactivated"} admin account {target.email}',
        target_type='User', target_id=target.pk, target_repr=target.email,
    )
    messages.success(request, f'{target.email} {"activated" if active else "deactivated"}.')
    return redirect('dashboard:admin_internal_users')
