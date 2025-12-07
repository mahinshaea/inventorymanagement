from rest_framework import serializers
from .models import user, item, order

# Serializer for the 'user' model
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = user
        # Only expose safe fields (exclude password)
        fields = ['id', 'name', 'email', 'role']

# Serializer for the 'item' model (Inventory)
class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = item
        # Expose all fields for inventory management
        fields = '__all__'

# Serializer for the 'order' model
class OrderSerializer(serializers.ModelSerializer):
    # Use nested representation for foreign keys
    user = UserSerializer(read_only=True)
    delivery_boy = UserSerializer(read_only=True)
    item_name = serializers.CharField(source='item.name', read_only=True)

    class Meta:
        model = order
        fields = [
            'order_id', 'user', 'item', 'item_name', 'quantity', 
            'total_price', 'address', 'status', 'order_date', 'delivery_boy'
        ]
        # These fields are set by the server, not in the API creation request
        read_only_fields = ['total_price', 'status', 'order_date', 'user', 'delivery_boy']