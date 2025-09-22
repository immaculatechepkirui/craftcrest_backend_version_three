from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import User
from products.models import Inventory
from cart.models import ShoppingCart
from django.conf import settings
class Order(models.Model):
    ORDER_TYPE_CHOICES = [('ready-made', 'Ready-made'), ('custom', 'Custom')]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    cart = models.ForeignKey(ShoppingCart, on_delete=models.CASCADE, null=True, blank=True)
    buyer = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    null=True,
    blank=True,
    related_name='orders',
    limit_choices_to={'user_type': 'buyer'}

)
    artisan = models.ForeignKey(
    limit_choices_to={"user_type": "artisan"},
    on_delete=models.CASCADE,
    to=settings.AUTH_USER_MODEL,
    null=False,
    blank=False,
)

    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    rejection_reason = models.CharField(max_length=50, blank=True, null=True)
    delivery_confirmed = models.BooleanField(default=False)
    rejection_date = models.DateTimeField(blank=True, null=True)
    payment_status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
 
    def __str__(self):
        return f"Order {self.id}"

class CustomDesignRequest(models.Model):
    STATUS_CHOICES = [
        ('material-sourcing', 'Material-sourcing'),
        ('in-progress', 'In-progress'),
        ('rejected', 'Rejected'),
        ('accepted', 'Accepted'),
        ('completed', 'Completed'),
    ]
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='custom_requests_as_buyer',limit_choices_to={'user_type': 'buyer'}
        
    )
    artisan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='custom_requests_as_artisan',
        limit_choices_to={'user_type': 'artisan'}
    )
    description = models.TextField()
    reference_images = models.URLField(blank=True, null=True)
    deadline = models.DateField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='material_sourced')
    quote_amount = models.DecimalField(max_digits=10, decimal_places=2)
    material_price = models.DecimalField(max_digits=10, decimal_places=2)
    labour_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateField(auto_now_add=True)

class OrderStatus(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in-progress', 'In-progress'),
        ('completed', 'Completed')
    ]
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    artisan = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,limit_choices_to={'user_type': 'artisan'})
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='order_images/')
    buyer_approval = models.BooleanField(default=False)
    approval_timestamp = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Rating(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ratings_given',limit_choices_to={'user_type': 'buyer'})
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)