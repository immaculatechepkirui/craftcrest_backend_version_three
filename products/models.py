from django.db import models
from users.models import User
from django.conf import settings

class Inventory(models.Model):
    CATEGORY_CHOICES = [
    ('pottery', 'Pottery'),
    ('tailoring', 'Tailoring'),
    ('basketry', 'Basketry'),
    ('weaving', 'Weaving'),
    ('crocheting', 'Crocheting'),
    ('ceramics', 'Ceramics'),
    ('jewelry','jewerly'),
   
]

    artisan = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField()
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    is_customizable = models.BooleanField(default=False)
    custom_options = models.TextField(blank=True, null=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product_name
    