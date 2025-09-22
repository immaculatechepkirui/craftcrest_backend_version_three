from django.contrib import admin
from .models import CustomDesignRequest, Order, OrderStatus,Rating

admin.site.register(CustomDesignRequest)
admin.site.register(Order)
admin.site.register(OrderStatus)
admin.site.register(Rating)