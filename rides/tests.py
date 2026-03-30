from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from accounts.models import DriverProfile

from .models import Ride
from .services import maybe_advance_ride_status

User = get_user_model()


class RideBookingTests(TestCase):
    def setUp(self):
        self.driver = User.objects.create_user(
            username="driver1",
            password="testpass123",
            is_driver=True,
        )
        DriverProfile.objects.create(
            user=self.driver,
            vehicle_number="KA01AB1234",
            is_available=True,
        )
        self.rider = User.objects.create_user(
            username="rider1",
            password="testpass123",
            is_driver=False,
        )

    def test_book_redirects_if_not_logged_in(self):
        c = Client()
        r = c.get("/rides/book/", follow=False)
        self.assertEqual(r.status_code, 302)

    def test_book_assigns_available_driver(self):
        c = Client()
        c.login(username="rider1", password="testpass123")
        r = c.post(
            "/rides/book/",
            {
                "pickup_location": "MG Road",
                "drop_location": "Airport",
                "action": "confirm",
            },
        )
        self.assertEqual(r.status_code, 302)
        ride = Ride.objects.get()
        self.assertEqual(ride.driver_id, self.driver.id)
        self.assertEqual(ride.status, Ride.Status.PENDING)

    def test_no_driver_shows_error(self):
        DriverProfile.objects.update(is_available=False)
        c = Client()
        c.login(username="rider1", password="testpass123")
        r = c.post(
            "/rides/book/",
            {
                "pickup_location": "MG Road",
                "drop_location": "Airport",
                "action": "confirm",
            },
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Ride.objects.count(), 0)

    def test_status_api_updates(self):
        c = Client()
        c.login(username="rider1", password="testpass123")
        c.post(
            "/rides/book/",
            {
                "pickup_location": "MG Road",
                "drop_location": "Airport",
                "action": "confirm",
            },
        )
        ride = Ride.objects.get()
        r = c.get(f"/rides/{ride.pk}/status/api/")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("status", data)


class StatusSimulationTests(TestCase):
    def test_advance_to_completed(self):
        user = User.objects.create_user(username="u", password="p")
        driver = User.objects.create_user(username="d", password="p", is_driver=True)
        ride = Ride.objects.create(
            user=user,
            driver=driver,
            pickup_location="A",
            drop_location="B",
            status=Ride.Status.PENDING,
            fare=100,
        )
        from django.utils import timezone
        from datetime import timedelta

        ride.created_at = timezone.now() - timedelta(seconds=15)
        ride.save(update_fields=["created_at"])
        maybe_advance_ride_status(ride)
        ride.refresh_from_db()
        self.assertEqual(ride.status, Ride.Status.COMPLETED)
