import shutil
import tempfile
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Car, CarPhoto, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp()


def tearDownModule():
    shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)


def fake_image(name: str) -> SimpleUploadedFile:
    """Return a minimal valid GIF image to satisfy ImageField validation."""
    gif_bytes = (
        b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00"
        b"\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x0a\x00\x01\x00,"
        b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02L\x01\x00;"
    )
    return SimpleUploadedFile(name, gif_bytes, content_type="image/gif")


class CarListingViewTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin",
            password="secret",
            role=User.Roles.ADMIN,
        )
        self.car_active = Car.objects.create(
            license_plate="1234ABC",
            brand="Seat",
            model_name="Ibiza",
            kilometers=45000,
            year=2019,
            price=15000,
            created_by=self.admin,
            is_active=True,
        )
        self.car_other = Car.objects.create(
            license_plate="5678XYZ",
            brand="Audi",
            model_name="A3",
            kilometers=22000,
            year=2021,
            price=28000,
            created_by=self.admin,
            is_active=False,
        )

    def test_home_view_lists_only_active_cars(self):
        response = self.client.get(reverse("listings:home"))
        self.assertEqual(response.status_code, 200)
        cars = response.context["cars"]
        self.assertIn(self.car_active, cars)
        self.assertNotIn(self.car_other, cars)

    def test_filter_by_brand(self):
        url = reverse("listings:home")
        response = self.client.get(url, {"brand": "Seat"})
        self.assertContains(response, "Seat")
        self.assertNotContains(response, "Audi")

    def test_filter_by_year_range(self):
        older = Car.objects.create(
            license_plate="0000BBB",
            brand="Seat",
            model_name="Leon",
            kilometers=80000,
            year=2010,
            price=9500,
            created_by=self.admin,
            is_active=True,
        )
        response = self.client.get(reverse("listings:home"), {"year_min": 2015})
        self.assertIn(self.car_active, response.context["cars"])
        self.assertNotIn(older, response.context["cars"])


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class CarPhotoLimitTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="photo-admin",
            password="secret",
            role=User.Roles.ADMIN,
        )
        self.car = Car.objects.create(
            license_plate="8888TTT",
            brand="Tesla",
            model_name="Model 3",
            kilometers=1000,
            year=2022,
            price=45000,
            created_by=self.admin,
            is_active=True,
        )

    def test_car_photo_limit_validation(self):
        for i in range(Car.MAX_PHOTOS):
            CarPhoto.objects.create(
                car=self.car,
                image=fake_image(f"photo_{i}.gif"),
                position=i,
            )

        exceeding = CarPhoto(
            car=self.car,
            image=fake_image("overflow.gif"),
            position=99,
        )

        with self.assertRaises(ValidationError):
            exceeding.clean()


class CheckoutViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="buyer",
            password="secret",
            role=User.Roles.REGISTERED,
            email="buyer@example.com",
        )
        self.car = Car.objects.create(
            license_plate="1111AAA",
            brand="BMW",
            model_name="Serie 1",
            kilometers=30000,
            year=2020,
            price=23000,
            is_active=True,
        )

    def test_buy_requires_login(self):
        response = self.client.get(reverse("listings:car_buy", args=[self.car.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    @override_settings(
        STRIPE_SECRET_KEY="sk_test",
        STRIPE_PUBLISHABLE_KEY="pk_test",
        STRIPE_SUCCESS_URL="https://example.com/success",
        STRIPE_CANCEL_URL="https://example.com/cancel",
    )
    def test_checkout_session_creation(self):
        self.client.login(username="buyer", password="secret")
        mock_session = type("obj", (), {"id": "sess_123"})()
        with patch("listings.views.stripe.checkout.Session.create") as mock_create:
            mock_create.return_value = mock_session
            response = self.client.post(
                reverse("listings:checkout_session", args=[self.car.pk])
            )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"sessionId": "sess_123"})
