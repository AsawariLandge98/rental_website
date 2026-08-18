from django.contrib import admin

from .models import Payment, Subscription, SubscriptionPlan


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'listing_limit', 'priority_listing', 'is_active', 'order']
    list_filter = ['is_active', 'priority_listing']
    search_fields = ['name']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['owner', 'plan', 'status', 'started_at', 'current_period_end']
    list_filter = ['status', 'plan']
    search_fields = ['owner__email', 'owner__full_name']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['owner', 'plan', 'amount', 'status', 'razorpay_order_id', 'created_at']
    list_filter = ['status']
    search_fields = ['owner__email', 'razorpay_order_id', 'razorpay_payment_id']

    def has_add_permission(self, request):
        # Payment rows are only ever created by the real Razorpay order/verify
        # flow (subscriptions/views.py) — never hand-typed.
        return False
