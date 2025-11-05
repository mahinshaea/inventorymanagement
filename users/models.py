from django.db import models
role_choices = [
    ('admin', 'Admin'),
    ('manager', 'Manager'),
    ('customer', 'Customer'),
    ('deliveryboy', 'Delivery'),
]
# Create your models here.
class user(models.Model):
    name = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    role = models.CharField(max_length=20, choices=role_choices,default='customer')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name
class item(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    expirydate = models.DateField()
    quantity = models.IntegerField()
    image_path = models.ImageField(upload_to='item_images/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name
class order(models.Model):
    order_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('users.user', on_delete=models.CASCADE)
    item = models.ForeignKey('users.item', on_delete=models.CASCADE)
    address = models.TextField()
    quantity = models.IntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    order_date = models.DateTimeField(auto_now_add=True)
    delivery_boy = models.ForeignKey('users.user', on_delete=models.SET_NULL, null=True, blank=True, related_name='deliveries')
    status = models.CharField(max_length=50, default='Pending', choices=[
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    ])
    def __str__(self):
        return f"Order {self.order_id} by {self.user.name}"
    