from django.db import models
from users.models import User
from products.models import Inventory
from django.conf import settings

class Item(models.Model):

    inventory = models.ForeignKey(Inventory,null=True, on_delete=models.PROTECT)
    quantity=models.PositiveIntegerField()
    total_price=models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        self.total_price=self.inventory.price * self.quantity
        super().save(*args, **kwargs)
       
    
class ShoppingCart(models.Model):
    user = models.ForeignKey(
    settings.AUTH_USER_MODEL,
     null=True,  
    blank=True,
    on_delete=models.CASCADE,
    limit_choices_to={'user_type': 'buyer'}
)

    item=models.ManyToManyField(Item, related_name='item')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):

        if self.user is not None:
            return f"{self.user.first_name}'s shopping cart"
        return "Shopping cart with no user"
 