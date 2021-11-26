from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id_product', 'available', 'new_price', 'note', 'refresh_date')
    list_filter = ('available', 'refresh_date')
