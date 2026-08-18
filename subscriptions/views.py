import razorpay
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from dashboard.decorators import owner_or_hotel_required
from .models import Payment, Subscription, SubscriptionPlan


def _razorpay_client():
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        return None
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def _current_subscription(user):
    return Subscription.objects.filter(
        owner=user, status=Subscription.Status.ACTIVE, current_period_end__gt=timezone.now(),
    ).select_related('plan').first()


@owner_or_hotel_required
def plan_list(request):
    context = {
        'plans': SubscriptionPlan.objects.filter(is_active=True),
        'current_subscription': _current_subscription(request.user),
        'razorpay_configured': _razorpay_client() is not None,
    }
    return render(request, 'dashboard/owner_subscription.html', context)


@owner_or_hotel_required
@require_POST
def create_order(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, pk=plan_id, is_active=True)
    client = _razorpay_client()
    if client is None:
        return JsonResponse(
            {'error': "Payments aren't configured yet — the platform's Razorpay test-mode keys haven't been added."},
            status=503,
        )

    amount_paise = int(plan.price * 100)
    order = client.order.create({'amount': amount_paise, 'currency': 'INR', 'payment_capture': 1})
    payment = Payment.objects.create(
        owner=request.user, plan=plan, razorpay_order_id=order['id'], amount=plan.price,
    )
    return JsonResponse({
        'order_id': order['id'],
        'amount': amount_paise,
        'currency': 'INR',
        'key_id': settings.RAZORPAY_KEY_ID,
        'payment_id': payment.pk,
        'name': 'Rentora',
        'description': f'{plan.name} Plan Subscription',
        'prefill_name': request.user.full_name,
        'prefill_email': request.user.email,
    })


@owner_or_hotel_required
@require_POST
def verify_payment(request):
    payment = get_object_or_404(Payment, pk=request.POST.get('payment_id'), owner=request.user)

    if payment.status == Payment.Status.PAID:
        # Already processed (e.g. a repeated callback) — idempotent no-op.
        return JsonResponse({'ok': True, 'redirect_url': '/owner/dashboard/subscription/'})

    razorpay_order_id = request.POST.get('razorpay_order_id', '')
    razorpay_payment_id = request.POST.get('razorpay_payment_id', '')
    razorpay_signature = request.POST.get('razorpay_signature', '')

    # The signature only proves *some* order/payment pair from Razorpay is
    # genuine — it does NOT prove it's the order we created for *this*
    # Payment row. Without this check, a real signature from a cheap plan's
    # order could be replayed to activate a different, more expensive plan.
    if razorpay_order_id != payment.razorpay_order_id:
        return JsonResponse({'ok': False, 'error': 'Order does not match this payment.'}, status=400)

    client = _razorpay_client()
    if client is None:
        return JsonResponse({'ok': False, 'error': 'Payments are not configured.'}, status=503)

    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature,
        })
    except razorpay.errors.SignatureVerificationError:
        payment.status = Payment.Status.FAILED
        payment.save(update_fields=['status', 'updated_at'])
        return JsonResponse({'ok': False, 'error': 'Payment verification failed.'}, status=400)

    subscription = Subscription.objects.create(
        owner=request.user, plan=payment.plan, current_period_end=timezone.now() + timezone.timedelta(days=30),
    )
    payment.razorpay_payment_id = razorpay_payment_id
    payment.razorpay_signature = razorpay_signature
    payment.status = Payment.Status.PAID
    payment.subscription = subscription
    payment.save(update_fields=['razorpay_payment_id', 'razorpay_signature', 'status', 'subscription', 'updated_at'])

    messages.success(request, f'Subscribed to the {payment.plan.name} plan!')
    return JsonResponse({'ok': True, 'redirect_url': '/owner/dashboard/subscription/'})
