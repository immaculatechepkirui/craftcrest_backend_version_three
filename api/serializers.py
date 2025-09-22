
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from datetime import timedelta
from users.utils import send_otp_email
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework.authtoken.models import Token
from users.models import User, ArtisanPortfolio, Profile, PortfolioImage, ArtisanProfile
from users.utils import send_otp_email
from rest_framework import serializers

from django.conf import settings
import requests
from products.models import Inventory
from cart.models import ShoppingCart , Item
from django.conf import settings
from orders.models import Order, Rating, OrderStatus, CustomDesignRequest
from orders.models import Order

from .daraja import DarajaAPI
from payments.models import Payment
from orders.models import Order



class PortfolioImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioImage
        fields = ["id", "image"]
        read_only_fields = ["id"]

class ArtisanPortfolioSerializer(serializers.ModelSerializer):
    image_files = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=True,
        min_length=10 
    )
    images = PortfolioImageSerializer(many=True, read_only=True)

    class Meta:
        model = ArtisanPortfolio
        fields = ["id", "title", "description", "created_at", "image_files", "images", "artisan"]
        read_only_fields = ["id", "created_at", "images", "artisan"]

    def create(self, validated_data):
        image_files = validated_data.pop("image_files", [])
        artisan = validated_data.pop("artisan", None)  
        if artisan is None:
            raise serializers.ValidationError({"artisan": "Artisan is required to create a portfolio."})
        portfolio = ArtisanPortfolio.objects.create(artisan=artisan, **validated_data)
        for image_file in image_files:
            PortfolioImage.objects.create(portfolio=portfolio, image=image_file)
        return portfolio

    def validate(self, attrs):
        if not attrs.get("title"):
            raise serializers.ValidationError({"title": "Title is required."})
        if not attrs.get("description"):
            raise serializers.ValidationError({"description": "Description is required."})
        image_files = attrs.get("image_files", [])
        if len(image_files) < 10:
            raise serializers.ValidationError({
                "image_files": "At least 10 images are required for the portfolio."
            })
        return attrs


class UserRegistrationSerializer(serializers.ModelSerializer):
    token = serializers.SerializerMethodField(read_only=True)
    password = serializers.CharField(write_only=True, required=True)
    portfolio = ArtisanPortfolioSerializer(write_only=True, required=False)
    latitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True
    )
    longitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True
    )
    national_id = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[UniqueValidator(queryset=User.objects.all(), message="National ID already exists.")]
    )
    phone_number = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all(), message="Phone number already exists.")]
    )
    image = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = User
        fields = [
            "id", "token", "email", "password", "first_name", "last_name",
            "user_type", "phone_number", "image",
            "latitude", "longitude", "national_id", "portfolio"
        ]
        read_only_fields = ["id", "token"]

    def get_token(self, obj):
        token, _ = Token.objects.get_or_create(user=obj)
        return token.key

    def validate_email(self, value):
        validate_email(value)
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def validate_phone_number(self, value):
        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError("Phone number must be exactly 10 digits.")
        return value

    def create(self, validated_data):
        portfolio_data = validated_data.pop("portfolio", None)
        latitude = validated_data.pop("latitude", None)
        longitude = validated_data.pop("longitude", None)
        password = validated_data.pop("password")
        
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.is_active = False
        user.save()

        if user.user_type == User.ARTISAN:
            ArtisanProfile.objects.create(
                user=user,
                latitude=latitude,
                longitude=longitude
            )
            if portfolio_data:
                portfolio_serializer = ArtisanPortfolioSerializer(data=portfolio_data)
                portfolio_serializer.is_valid(raise_exception=True)
                portfolio_serializer.save(artisan=user)
                profile, _ = ArtisanProfile.objects.get_or_create(user=user)

        user.generate_otp()
        send_otp_email(user.email, user.otp, purpose='verify')
        return user

   
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        phone_number = data.get("phone_number")
        password = data.get("password")

        if (email and phone_number) or (not email and not phone_number):
            raise serializers.ValidationError({"non_field_errors": "Must provide either email or phone number, but not both."})

        if not password:
            raise serializers.ValidationError({"non_field_errors": "Must provide password."})

        try:
            if email:
                user = User.objects.get(email=email)
            else:
                user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            raise serializers.ValidationError({"non_field_errors": "Invalid email/phone or password."})

        if not user.is_active or not user.check_password(password):
            raise serializers.ValidationError({"non_field_errors": "Invalid email/phone or password."})

        token, _ = Token.objects.get_or_create(user=user)
        data["user"] = user
        data["token"] = token.key
        return data

class CustomUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = User
        fields = ["email", "full_name", "phone_number", "image", "user_type"]
        read_only_fields = ["email", "user_type", "image"]

    def get_full_name(self, obj):
        return f"{obj.first_name or ''} {obj.last_name or ''}".strip()

class ProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Profile
        fields = ["id", "user", "image"]
        read_only_fields = ["id", "user"]

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        try:
            user.generate_otp()
            send_otp_email(user.email, user.otp, purpose='reset')
        except Exception as e:
            raise serializers.ValidationError(f"Failed to send OTP email: {str(e)}")
        return value

class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    def validate(self, data):
        try:
            user = User.objects.get(email=data["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "User with this email does not exist."})
        if not user.otp or user.otp != data["otp"]:
            raise serializers.ValidationError({"otp": "Invalid OTP."})
        if not user.otp_exp or user.otp_exp < timezone.now():
            raise serializers.ValidationError({"otp": "OTP has expired."})
        user.otp_verified = True
        user.is_active = True
        user.otp = None
        user.otp_exp = None
        user.save(update_fields=["otp_verified", "is_active", "otp", "otp_exp"])
        return data

class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, data):
        try:
            user = User.objects.get(email=data["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "User not found."})
        if user.is_active:
            raise serializers.ValidationError({"email": "This account is already verified."})
        user.generate_otp()
        send_otp_email(user.email, user.otp, purpose='verify')
        return {"message": "A new OTP has been sent to your email."}

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data.get("new_password") != data.get("confirm_password"):
            raise serializers.ValidationError({"confirm_password": "Passwords must match."})
        try:
            user = User.objects.get(email=data["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "User with this email does not exist."})
        if not user.otp_verified:
            raise serializers.ValidationError({"email": "OTP not verified."})
        try:
            validate_password(data["new_password"], user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"new_password": list(exc.messages)})
        return data

    def save(self, **kwargs):
        user = User.objects.get(email=self.validated_data["email"])
        user.set_password(self.validated_data["new_password"])
        user.otp = None
        user.otp_exp = None
        user.otp_verified = False
        user.save()
        return user

class UserSerializer(serializers.ModelSerializer):
    latitude = serializers.DecimalField(source='artisanprofile.latitude', max_digits=9, decimal_places=6, read_only=True)
    longitude = serializers.DecimalField(source='artisanprofile.longitude', max_digits=9, decimal_places=6, read_only=True)
    address = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'id', 'user_type', 'first_name', 'last_name', 'email', 'phone_number',
            'national_id', 'image', 'otp_verified', 'otp_exp',
            'address', 'latitude', 'longitude',
        ]
        read_only_fields = ['otp_verified', 'otp_exp']

    def create(self, validated_data):
        address = validated_data.pop('address', None)
        user = User.objects.create(**validated_data)

        if address:
            lat, lon = self.geocode_address(address)
            if lat is not None and lon is not None:
                profile, _ = ArtisanProfile.objects.get_or_create(user=user)
                profile.latitude = lat
                profile.longitude = lon
                profile.save()

        return user


    def update(self, instance, validated_data):
        address = validated_data.pop('address', None)
        instance = super().update(instance, validated_data)

        if address:
            lat, lon = self.geocode_address(address)
            if lat is not None and lon is not None:
                profile, _ = ArtisanProfile.objects.get_or_create(user=instance)
                profile.latitude = lat
                profile.longitude = lon
                profile.save()

        return instance

    def geocode_address(self, address):
        if not address:
            return None, None
        LOCATIONIQ_API_KEY = settings.LOCATIONIQ_API_KEY
        url = "https://us1.locationiq.com/v1/search.php"
        params = {
            'key': LOCATIONIQ_API_KEY,
            'q': address,
            'format': 'json',
            'limit': 1,
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
        except requests.RequestException:
            pass
        return None, None

class NearbyArtisanSearchSerializer(serializers.Serializer):
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    radius = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, default=50)  


class ShoppingCartSerializer(serializers.ModelSerializer):
    item = serializers.PrimaryKeyRelatedField(many=True, queryset=Item.objects.all())
    class Meta:
        model = ShoppingCart
        fields = '__all__'
    def update(self, instance, validated_data):
        items = validated_data.pop('item', None)
        if items is not None:
            instance.item.set(items)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
    
class ItemSerializer (serializers.ModelSerializer):
    class Meta:
        model= Item
        fields = ['id','inventory','quantity','total_price']      

class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = '__all__'



class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'

    def validate_order_type(self, value):
        if value not in ['ready-made', 'custom']:
            raise serializers.ValidationError("Invalid order_type")
        return value

    def validate(self, value):
        status = value.get('status')
        payment_status = value.get('payment_status')
        order_type = value.get('order_type')

        if status == 'confirmed' and payment_status != 'completed':
            raise serializers.ValidationError(
                "Payment must be completed if order status is confirmed."
            )

        if status == 'rejected':
            if not value.get('rejected_reason') or not value.get('rejected_date'):
                raise serializers.ValidationError(
                    "Rejected orders must have reason and date."
                )

        return value


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = '__all__'
        

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatus
        fields ='__all__'
       

class CustomDesignRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomDesignRequest
        fields = '__all__'
        read_only_fields = ['request_id', 'created_at']




class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['id', 'paid_at', 'released_at', 'transaction_date']

class STKPushSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    buyer_phone = serializers.CharField(max_length=15, required=False)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    transaction_code = serializers.CharField(max_length=100)
    transaction_desc = serializers.CharField(max_length=255)

    def validate(self, data):
        try:
            order = Order.objects.get(id=data['order_id'])
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order does not exist")
        buyer = order.buyer
        artisan = order.artisan
        data['order_obj'] = order
        data['artisan_obj'] = artisan
        if not data.get('buyer_phone'):
            data['buyer_phone'] = buyer.phone_number
        return data

class DeliveryConfirmSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()

class RefundSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    reason = serializers.CharField(max_length=255)

class B2CPaymentSerializer(serializers.Serializer):
    artisan_phone = serializers.CharField(max_length=15)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = serializers.CharField(max_length=100)
    transaction_desc = serializers.CharField(max_length=255, required=False)
    occassion = serializers.CharField(max_length=255, required=False)

class DeliveryConfirmSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()

class RefundSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    reason = serializers.CharField(max_length=255)
