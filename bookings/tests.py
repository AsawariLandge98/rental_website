from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from properties.models import Property
from .models import Booking


class BookingRequestTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123',
            full_name='Test Owner', role=User.Role.OWNER,
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )
        self.hotel = Property.objects.create(
            owner=self.owner, title='Lakeview Homestay', status=Property.Status.PUBLISHED,
            category=Property.Category.HOMESTAY, city='Nagpur', nightly_rate=2000,
        )
        self.rental = Property.objects.create(
            owner=self.owner, title='2BHK Flat', status=Property.Status.PUBLISHED,
            category=Property.Category.RESIDENTIAL, city='Nagpur', monthly_rent=15000,
        )
        self.client.force_login(self.tenant)

    def _dates(self, start_offset=2, nights=3):
        check_in = date.today() + timedelta(days=start_offset)
        check_out = check_in + timedelta(days=nights)
        return check_in.isoformat(), check_out.isoformat()

    def test_request_booking_succeeds_for_a_bookable_property(self):
        check_in, check_out = self._dates()
        response = self.client.post(reverse('bookings:request_booking', args=[self.hotel.pk]), {
            'check_in': check_in, 'check_out': check_out, 'guests': 2, 'message': 'Anniversary trip',
        })
        self.assertRedirects(response, reverse('properties:detail', args=[self.hotel.pk]))
        booking = Booking.objects.get(tenant=self.tenant, property=self.hotel)
        self.assertEqual(booking.status, Booking.Status.PENDING)
        self.assertEqual(booking.guests, 2)
        self.assertEqual(booking.nights(), 3)
        self.assertEqual(booking.total_price(), 6000)
        self.assertTrue(self.tenant.notifications.filter(category='visit').exists())
        self.assertTrue(self.owner.notifications.filter(category='visit', message__icontains=self.tenant.full_name).exists())

    def test_cannot_request_booking_on_a_non_bookable_property(self):
        check_in, check_out = self._dates()
        response = self.client.post(reverse('bookings:request_booking', args=[self.rental.pk]), {
            'check_in': check_in, 'check_out': check_out, 'guests': 1,
        })
        self.assertEqual(response.status_code, 404)

    def test_check_in_in_the_past_is_rejected(self):
        past = (date.today() - timedelta(days=1)).isoformat()
        future = (date.today() + timedelta(days=2)).isoformat()
        response = self.client.post(reverse('bookings:request_booking', args=[self.hotel.pk]), {
            'check_in': past, 'check_out': future, 'guests': 1,
        })
        self.assertRedirects(response, reverse('properties:detail', args=[self.hotel.pk]))
        self.assertFalse(Booking.objects.filter(property=self.hotel).exists())

    def test_check_out_before_check_in_is_rejected(self):
        check_in, check_out = self._dates()
        response = self.client.post(reverse('bookings:request_booking', args=[self.hotel.pk]), {
            'check_in': check_out, 'check_out': check_in, 'guests': 1,
        })
        self.assertRedirects(response, reverse('properties:detail', args=[self.hotel.pk]))
        self.assertFalse(Booking.objects.filter(property=self.hotel).exists())

    def test_overlapping_confirmed_booking_is_rejected(self):
        check_in, check_out = self._dates()
        Booking.objects.create(
            tenant=self.tenant, property=self.hotel,
            check_in=date.fromisoformat(check_in), check_out=date.fromisoformat(check_out),
            status=Booking.Status.CONFIRMED,
        )
        other_tenant = User.objects.create_user(
            email='other@example.com', password='StrongPass123', full_name='Other Tenant', role=User.Role.TENANT,
        )
        self.client.force_login(other_tenant)
        response = self.client.post(reverse('bookings:request_booking', args=[self.hotel.pk]), {
            'check_in': check_in, 'check_out': check_out, 'guests': 1,
        })
        self.assertRedirects(response, reverse('properties:detail', args=[self.hotel.pk]))
        self.assertEqual(Booking.objects.filter(property=self.hotel, tenant=other_tenant).count(), 0)

    def test_overlapping_pending_booking_is_still_allowed(self):
        # Only CONFIRMED bookings block a new request — two tenants can both
        # have a PENDING request for the same dates; the host's Confirm
        # action (dashboard/views.py::owner_booking_confirm) is where the
        # second overlap gets caught.
        check_in, check_out = self._dates()
        Booking.objects.create(
            tenant=self.tenant, property=self.hotel,
            check_in=date.fromisoformat(check_in), check_out=date.fromisoformat(check_out),
            status=Booking.Status.PENDING,
        )
        other_tenant = User.objects.create_user(
            email='other@example.com', password='StrongPass123', full_name='Other Tenant', role=User.Role.TENANT,
        )
        self.client.force_login(other_tenant)
        response = self.client.post(reverse('bookings:request_booking', args=[self.hotel.pk]), {
            'check_in': check_in, 'check_out': check_out, 'guests': 1,
        })
        self.assertRedirects(response, reverse('properties:detail', args=[self.hotel.pk]))
        self.assertTrue(Booking.objects.filter(property=self.hotel, tenant=other_tenant).exists())

    def test_login_required(self):
        self.client.logout()
        check_in, check_out = self._dates()
        response = self.client.post(reverse('bookings:request_booking', args=[self.hotel.pk]), {
            'check_in': check_in, 'check_out': check_out, 'guests': 1,
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)


class MyBookingsAndCancelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123', full_name='Owner', role=User.Role.OWNER,
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123', full_name='Tenant', role=User.Role.TENANT,
        )
        self.hotel = Property.objects.create(
            owner=self.owner, title='Lakeview Homestay', status=Property.Status.PUBLISHED,
            category=Property.Category.HOMESTAY, city='Nagpur', nightly_rate=2000,
        )
        self.booking = Booking.objects.create(
            tenant=self.tenant, property=self.hotel,
            check_in=date.today() + timedelta(days=2), check_out=date.today() + timedelta(days=5),
        )
        self.client.force_login(self.tenant)

    def test_my_bookings_lists_only_the_tenants_own_bookings(self):
        other_tenant = User.objects.create_user(
            email='other@example.com', password='StrongPass123', full_name='Other', role=User.Role.TENANT,
        )
        Booking.objects.create(
            tenant=other_tenant, property=self.hotel,
            check_in=date.today() + timedelta(days=10), check_out=date.today() + timedelta(days=12),
        )
        response = self.client.get(reverse('bookings:my_bookings'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['bookings']), [self.booking])

    def test_tenant_can_cancel_own_pending_booking(self):
        response = self.client.post(reverse('bookings:cancel_booking', args=[self.booking.pk]))
        self.assertRedirects(response, reverse('bookings:my_bookings'))
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.CANCELLED)

    def test_cannot_cancel_a_declined_booking(self):
        self.booking.status = Booking.Status.DECLINED
        self.booking.save(update_fields=['status'])
        response = self.client.post(reverse('bookings:cancel_booking', args=[self.booking.pk]))
        self.assertRedirects(response, reverse('bookings:my_bookings'))
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.DECLINED)

    def test_cannot_cancel_another_tenants_booking(self):
        other_tenant = User.objects.create_user(
            email='other@example.com', password='StrongPass123', full_name='Other', role=User.Role.TENANT,
        )
        self.client.force_login(other_tenant)
        response = self.client.post(reverse('bookings:cancel_booking', args=[self.booking.pk]))
        self.assertEqual(response.status_code, 404)
