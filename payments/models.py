from django.db import models
from django.conf import settings
from orders.models import Order
from users.models import User

class Payment(models.Model):
    artisan = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'artisan'},
        related_name='artisan_payments'
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        null=True,
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_code = models.CharField(max_length=50)
    status = models.CharField(max_length=20)
    paid_at = models.DateTimeField()
    released_at = models.DateTimeField(null=True, blank=True)
    held_by_platform = models.BooleanField(default=True)

    def __str__(self):
        return f"Payment of {self.amount} by {self.artisan}"
