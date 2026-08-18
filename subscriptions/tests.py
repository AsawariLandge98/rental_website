from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from .models import Payment, Subscription, SubscriptionPlan


class SeedPlanTests(TestCase):
    def test_seed_migration_created_four_real_plans(self):
        names = set(SubscriptionPlan.objects.values_list('name', flat=True))
        self.assertEqual(names, {'Free', 'Silver', 'Gold', 'Premium'})
        free = SubscriptionPlan.objects.get(name='Free')
        self.assertEqual(free.price, 0)
        self.assertEqual(free.listing_limit, 3)
        premium = SubscriptionPlan.objects.get(name='Premium')
        self.assertIsNone(premium.listing_limit)


class PlanListAccessTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123',
            full_name='Test Owner', role=User.Role.OWNER,
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )

    def test_owner_can_view_plans(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('subscriptions:plan_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Free')
        self.assertContains(response, 'Premium')

    def test_tenant_cannot_view_plans(self):
        self.client.force_login(self.tenant)
        response = self.client.get(reverse('subscriptions:plan_list'))
        self.assertEqual(response.status_code, 403)

    def test_gateway_not_configured_by_default_in_tests(self):
        # No RAZORPAY_KEY_ID/SECRET set in the test environment — the page
        # must say so honestly rather than offering a checkout that'll fail.
        self.client.force_login(self.owner)
        response = self.client.get(reverse('subscriptions:plan_list'))
        self.assertFalse(response.context['razorpay_configured'])
        self.assertContains(response, "Payments aren't switched on yet")


class CreateOrderTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123',
            full_name='Test Owner', role=User.Role.OWNER,
        )
        self.plan = SubscriptionPlan.objects.get(name='Gold')
        self.client.force_login(self.owner)

    def test_create_order_fails_gracefully_without_configured_keys(self):
        response = self.client.post(reverse('subscriptions:create_order', args=[self.plan.pk]))
        self.assertEqual(response.status_code, 503)
        self.assertIn('error', response.json())
        self.assertFalse(Payment.objects.exists())

    @patch('subscriptions.views._razorpay_client')
    def test_create_order_creates_a_real_payment_row(self, mock_client_factory):
        mock_client = mock_client_factory.return_value
        mock_client.order.create.return_value = {'id': 'order_test123'}
        response = self.client.post(reverse('subscriptions:create_order', args=[self.plan.pk]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['order_id'], 'order_test123')
        self.assertEqual(data['amount'], int(self.plan.price * 100))
        payment = Payment.objects.get(razorpay_order_id='order_test123')
        self.assertEqual(payment.owner, self.owner)
        self.assertEqual(payment.plan, self.plan)
        self.assertEqual(payment.status, Payment.Status.CREATED)


class VerifyPaymentTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123',
            full_name='Test Owner', role=User.Role.OWNER,
        )
        self.plan = SubscriptionPlan.objects.get(name='Gold')
        self.payment = Payment.objects.create(
            owner=self.owner, plan=self.plan, razorpay_order_id='order_real123', amount=self.plan.price,
        )
        self.client.force_login(self.owner)

    def test_order_id_mismatch_is_rejected_before_touching_razorpay(self):
        # Even with a technically-valid-looking signature payload, a
        # mismatched order_id must never activate a subscription — this is
        # the guard against replaying a cheap plan's real signature against
        # a different (more expensive) local Payment row.
        response = self.client.post(reverse('subscriptions:verify_payment'), {
            'payment_id': self.payment.pk,
            'razorpay_order_id': 'order_different456',
            'razorpay_payment_id': 'pay_x',
            'razorpay_signature': 'sig_x',
        })
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['ok'])
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.CREATED)
        self.assertFalse(Subscription.objects.exists())

    @patch('subscriptions.views._razorpay_client')
    def test_invalid_signature_marks_payment_failed(self, mock_client_factory):
        import razorpay
        mock_client = mock_client_factory.return_value
        mock_client.utility.verify_payment_signature.side_effect = razorpay.errors.SignatureVerificationError('bad')
        response = self.client.post(reverse('subscriptions:verify_payment'), {
            'payment_id': self.payment.pk,
            'razorpay_order_id': 'order_real123',
            'razorpay_payment_id': 'pay_x',
            'razorpay_signature': 'sig_forged',
        })
        self.assertEqual(response.status_code, 400)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.FAILED)
        self.assertFalse(Subscription.objects.exists())

    @patch('subscriptions.views._razorpay_client')
    def test_valid_signature_activates_a_real_subscription(self, mock_client_factory):
        mock_client = mock_client_factory.return_value
        mock_client.utility.verify_payment_signature.return_value = True
        response = self.client.post(reverse('subscriptions:verify_payment'), {
            'payment_id': self.payment.pk,
            'razorpay_order_id': 'order_real123',
            'razorpay_payment_id': 'pay_real789',
            'razorpay_signature': 'sig_real789',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.PAID)
        self.assertEqual(self.payment.razorpay_payment_id, 'pay_real789')

        subscription = Subscription.objects.get(owner=self.owner)
        self.assertEqual(subscription.plan, self.plan)
        self.assertEqual(subscription.status, Subscription.Status.ACTIVE)
        self.assertGreater(subscription.current_period_end, timezone.now())
        self.assertEqual(self.payment.subscription, subscription)

    @patch('subscriptions.views._razorpay_client')
    def test_repeated_verify_call_is_idempotent(self, mock_client_factory):
        mock_client = mock_client_factory.return_value
        mock_client.utility.verify_payment_signature.return_value = True
        payload = {
            'payment_id': self.payment.pk,
            'razorpay_order_id': 'order_real123',
            'razorpay_payment_id': 'pay_real789',
            'razorpay_signature': 'sig_real789',
        }
        self.client.post(reverse('subscriptions:verify_payment'), payload)
        self.client.post(reverse('subscriptions:verify_payment'), payload)
        self.assertEqual(Subscription.objects.filter(owner=self.owner).count(), 1)
