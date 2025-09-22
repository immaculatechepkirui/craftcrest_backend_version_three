import os
import requests
from api.daraja import DarajaAPI



import uuid
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from users.models import User, ArtisanProfile, Profile, ArtisanPortfolio, PortfolioImage
from api.serializers import UserRegistrationSerializer
from datetime import timedelta
from unittest.mock import patch
import os
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile

from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from users.models import User, ArtisanProfile, ArtisanPortfolio, PortfolioImage
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
from decimal import Decimal


def test_get_access_token():
    api = DarajaAPI()
    token = api.get_access_token()
    assert isinstance(token, str)
    assert len(token) > 10
    print("Access token:", token)
def test_stk_push():
    api = DarajaAPI()
    buyer_phone = os.environ.get("TEST_BUYER_PHONE", "254708374149")
    amount = 10
    transaction_id = "testtx001"
    transaction_desc = "Test payment"
    resp = api.stk_push(buyer_phone, amount, transaction_id, transaction_desc)
    print("STK Push response:", resp)
    assert "ResponseCode" in resp or "errorMessage" in resp
def test_b2c_payment():
    api = DarajaAPI()
    artisan_phone = os.environ.get("TEST_ARTISAN_PHONE", "254708374149")
    amount = 5
    transaction_id = "testtx002"
    transaction_desc = "Test B2C"
    resp = api.b2c_payment(artisan_phone, amount, transaction_id, transaction_desc)
    print("B2C response:", resp)
    assert "ResponseCode" in resp or "errorMessage" in resp
if __name__ == "__main__":
    test_get_access_token()
    test_stk_push()
    test_b2c_payment()



def create_test_image():
    file = BytesIO()
    image = Image.new('RGB', (100, 100), color='red')
    image.save(file, 'JPEG')
    file.seek(0)
    return SimpleUploadedFile(f"test_image.jpg", file.getvalue(), content_type="image/jpeg")

class UserModelTest(TestCase):
    def setUp(self):
        self.user_data = {
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Kinyanjui",
            "phone_number": "1234567890",
            "user_type": User.BUYER,
        }
        self.user = User.objects.create(**self.user_data)
        self.user.set_password("TestPassword123")
        self.user.save()

    def test_user_str(self):
        self.assertEqual(str(self.user), "John Kinyanjui (test@example.com)")

    def test_generate_otp(self):
        self.user.generate_otp()
        self.assertTrue(len(self.user.otp) == 6)
        self.assertFalse(self.user.otp_verified)
        self.assertTrue(self.user.otp_exp > timezone.now())

    def test_verify_otp_success(self):
        self.user.generate_otp()
        otp = self.user.otp
        result = self.user.verify_otp(otp)
        self.assertTrue(result)
        self.assertTrue(self.user.otp_verified)

    def test_verify_otp_expired(self):
        self.user.generate_otp()
        self.user.otp_exp = timezone.now() - timedelta(minutes=1)
        self.user.save()
        result = self.user.verify_otp(self.user.otp)
        self.assertFalse(result)
        self.assertFalse(self.user.otp_verified)

    def test_verify_otp_invalid(self):
        self.user.generate_otp()
        result = self.user.verify_otp("999999")
        self.assertFalse(result)
        self.assertFalse(self.user.otp_verified)


class ArtisanProfileModelTest(TestCase):
    def setUp(self):
        self.artisan = User.objects.create(
            email="artisan@example.com",
            first_name="John",
            last_name="Kinyanjui",
            phone_number="0987654321",
            user_type=User.ARTISAN
        )
        self.artisan.set_password("TestPassword123")
        self.artisan.save()
        self.artisan_profile = ArtisanProfile.objects.create(user=self.artisan)

    def test_artisan_profile_str(self):
        self.assertEqual(str(self.artisan_profile), "Artisan Profile for artisan@example.com")

    def test_clean_invalid_user_type(self):
        buyer = User.objects.create(
            email="buyer@example.com",
            first_name="Mary",
            last_name="Wanjiku",
            phone_number="1234567890",
            user_type=User.BUYER
        )
        buyer.set_password("TestPassword123")
        buyer.save()
        invalid_profile = ArtisanProfile(user=buyer)
        with self.assertRaisesMessage(Exception, "ArtisanProfile can only be linked to an artisan user."):
            invalid_profile.clean()

    def test_update_verification_status_verified(self):
        self.artisan_profile.fulfillment_rate = 95.0
        self.artisan_profile.rejection_rate = 5.0
        self.artisan_profile.average_rating = 4.5
        self.artisan_profile.days_active = 100
        self.artisan_profile.completed_orders = 15
        self.artisan_profile.update_verification_status()
        self.assertTrue(self.artisan_profile.is_verified)
        self.assertIsNone(self.artisan_profile.order_value_limit)

    def test_can_take_order_verified(self):
        self.artisan_profile.is_verified = True
        self.assertTrue(self.artisan_profile.can_take_order(3000))

    def test_can_take_order_unverified_limit(self):
        self.artisan_profile.is_verified = False
        self.artisan_profile.weekly_order_count = 3
        self.assertTrue(self.artisan_profile.can_take_order(1500))
        self.assertFalse(self.artisan_profile.can_take_order(2500))

    def test_can_take_order_unverified_weekly_limit(self):
        self.artisan_profile.is_verified = False
        self.artisan_profile.weekly_order_count = 5
        self.assertFalse(self.artisan_profile.can_take_order(1500))


class UserRegistrationSerializerTest(TestCase):
    def setUp(self):
        self.valid_data = {
            "email": "newuser@example.com",
            "password": "TestPassword123",
            "first_name": "John",
            "last_name": "Kinyanjui",
            "phone_number": "1234567890",
            "user_type": "buyer"
        }

    def test_valid_buyer_data(self):
        serializer = UserRegistrationSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())

    def test_valid_artisan_data(self):
        artisan_data = {
            **self.valid_data,
            "user_type": "artisan",
            "national_id": "1234567890",
            "latitude": 1.234567,
            "longitude": 2.345678,
            "portfolio": {
                "title": "Test Portfolio",
                "description": "A test portfolio",
                "image_files": [create_test_image() for _ in range(10)]  
            }
        }
        with patch('api.serializers.ArtisanPortfolioSerializer.is_valid', return_value=True):
            with patch('api.serializers.ArtisanPortfolioSerializer.validated_data', return_value={
                "title": "Test Portfolio",
                "description": "A test portfolio",
                "image_files": artisan_data["portfolio"]["image_files"]
            }):
                serializer = UserRegistrationSerializer(data=artisan_data)
                self.assertTrue(serializer.is_valid(), f"Serializer errors: {serializer.errors}")

    def test_missing_required_fields(self):
        invalid_data = {
            "email": "newuser@example.com",
            "password": "TestPassword123",
        }
        serializer = UserRegistrationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        expected_errors = ["first_name", "last_name", "phone_number", "user_type"]
        self.assertTrue(any(field in serializer.errors for field in expected_errors),
                        f"Expected one of {expected_errors}, got {serializer.errors}")

    def test_invalid_email(self):
        invalid_data = {**self.valid_data, "email": "invalid-email"}
        serializer = UserRegistrationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)


class UserRegistrationViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("register") 
        self.valid_buyer_data = {
            "email": "buyer@example.com",
            "password": "TestPassword123",
            "first_name": "John",
            "last_name": "Kinyanjui",
            "phone_number": "1234567890",
            "user_type": "buyer"
        }

    def test_register_buyer_success(self):
        with patch('users.utils.send_otp_email'):  
            response = self.client.post(self.url, self.valid_buyer_data, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn("id", response.data)
            self.assertIn("token", response.data)
            user = User.objects.get(email=self.valid_buyer_data["email"])
            self.assertFalse(user.is_active)

    def test_register_duplicate_email(self):
        User.objects.create(
            email="buyer@example.com",
            phone_number="0987654321",
            user_type=User.BUYER,
            first_name="Mary",
            last_name="Wanjiku"
        )
        with patch('users.utils.send_otp_email'):
            response = self.client.post(self.url, self.valid_buyer_data, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("email", response.data)


class LoginViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("login")
        self.user = User.objects.create(
            email="test@example.com",
            phone_number="1234567890",
            user_type=User.BUYER,
            is_active=True,
            first_name="John",
            last_name="Kinyanjui"
        )
        self.user.set_password("TestPassword123")
        self.user.save()

    def test_login_with_email_success(self):
        data = {"email": "test@example.com", "password": "TestPassword123"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertIn("user", response.data)

    def test_login_with_phone_success(self):
        data = {"phone_number": "1234567890", "password": "TestPassword123"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)

    def test_login_invalid_credentials(self):
        data = {"email": "test@example.com", "password": "WrongPassword"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)


class OTPVerificationViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("verify-otp")  
        self.user = User.objects.create(
            email="test@example.com",
            phone_number="1234567890",
            user_type=User.BUYER,
            is_active=False,
            first_name="John",
            last_name="Kinyanjui"
        )
        self.user.generate_otp()
        self.user.set_password("TestPassword123")
        self.user.save()

    def test_verify_otp_success(self):
        data = {"email": "test@example.com", "otp": self.user.otp}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.otp_verified)
        self.assertTrue(self.user.is_active)

    def test_verify_otp_invalid(self):
        data = {"email": "test@example.com", "otp": "999999"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("otp", response.data)

    def test_verify_otp_expired(self):
        self.user.otp_exp = timezone.now() - timedelta(minutes=1)
        self.user.save()
        data = {"email": "test@example.com", "otp": self.user.otp}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("otp", response.data)





class NearbyArtisansViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.artisan = User.objects.create(
            email="wanjikumwangi@gmail.com",
            user_type="artisan",
            first_name="Wanjiku",
            last_name="Mwangi",
            phone_number="0712345678"
        )
        ArtisanProfile.objects.create(
            user=self.artisan,
            latitude=-1.286389,
            longitude=36.817223
        )
        portfolio = ArtisanPortfolio.objects.create(
            artisan=self.artisan,
            title="Portfolio",
            description="Test"
        )
        PortfolioImage.objects.create(
            portfolio=portfolio,
            image=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
    def test_nearby_artisans_valid(self):
        data = {"latitude": -1.286389, "longitude": 36.817223, "radius": 100}
        response = self.client.post(reverse('nearby-artisans'), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['artisans']), 1)
        self.assertEqual(response.data['artisans'][0]['id'], self.artisan.id)
        self.assertAlmostEqual(response.data['artisans'][0]['distance_km'], 0.0, places=2)
    def test_nearby_artisans_no_results(self):
        data = {"latitude": 0.0, "longitude": 0.0, "radius": 10}
        response = self.client.post(reverse('nearby-artisans'), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['artisans']), 0)
    def test_nearby_artisans_invalid_input(self):
        data = {"latitude": -1.286389}
        response = self.client.post(reverse('nearby-artisans'), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('longitude', response.data)
    def test_nearby_artisans_invalid_coordinates(self):
        data = {"latitude": 100, "longitude": 36.817223, "radius": 50}
        response = self.client.post(reverse('nearby-artisans'), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['artisans']), 0)
class UserViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(
            email="kamaunjoroge@gmail.com",
            user_type="buyer",
            first_name="Kamau",
            last_name="Njoroge",
            phone_number="0723456789"
        )
        self.artisan = User.objects.create(
            email="muthoniwafula@gmail.com",
            user_type="artisan",
            first_name="Muthoni",
            last_name="Wafula",
            phone_number="0734567890"
        )
        ArtisanProfile.objects.create(
            user=self.artisan,
            latitude=-1.286389,
            longitude=36.817223
        )
    def test_list_users(self):
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertIn("kamaunjoroge@gmail.com", [user['email'] for user in response.data])
    def test_retrieve_user(self):
        response = self.client.get(reverse('user-detail', kwargs={'pk': self.artisan.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['email'], "muthoniwafula@gmail.com")
        self.assertEqual(response.data['latitude'], "-1.286389")
    @patch('requests.get')
    def test_create_user_with_address(self, mock_get):
        mock_get.return_value.json.return_value = [{'lat': '-1.286389', 'lon': '36.817223'}]
        mock_get.return_value.status_code = 200
        data = {
            "email": "njerikiplagat@gmail.com",
            "user_type": "artisan",
            "first_name": "Njeri",
            "last_name": "Kiplagat",
            "phone_number": "0745678901",
            "address": "Kenyatta Avenue, Nairobi"
        }
        response = self.client.post(reverse('user-list'), data, format='json')
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email="njerikiplagat@gmail.com")
        self.assertEqual(user.artisanprofile.latitude, Decimal('-1.286389'))
    def test_create_user_invalid_data(self):
        data = {
            "email": "invalid",
            "user_type": "buyer",
            "first_name": "Invalid",
            "last_name": "User"
        }
        response = self.client.post(reverse('user-list'), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.data)






