from django.contrib import admin
from .models import user, item, order


@admin.register(user)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'role', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('name', 'email')
    ordering = ('-created_at',)
    list_per_page = 20


@admin.register(item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'quantity', 'expirydate', 'updated_at')
    search_fields = ('name', 'description')
    list_filter = ('expirydate',)
    ordering = ('-updated_at',)
    list_per_page = 20


@admin.register(order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'item', 'quantity', 'total_price', 'status', 'order_date', 'delivery_boy')
    list_filter = ('status', 'order_date')
    search_fields = ('user__name', 'item__name', 'delivery_boy__name')
    ordering = ('-order_date',)
    list_per_page = 20

    # Optional: Display related user/item fields for better readability
    autocomplete_fields = ('user', 'item', 'delivery_boy')
