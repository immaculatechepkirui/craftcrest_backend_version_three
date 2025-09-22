from django.contrib import admin
from .models import Item
from .models import ShoppingCart
admin.site.register(ShoppingCart)
admin.site.register(Item)
