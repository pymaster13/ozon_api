from rest_framework import serializers
from .models import *

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id_product', 'available', 'new_price', 'note', 'refresh_date']
