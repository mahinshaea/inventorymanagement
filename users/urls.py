from django.urls import path
from . import views

urlpatterns = [
    path('', views.printhello, name='index'),  # Changed to root URL and renamed to 'index'
    path('register/', views.register, name='register'),
    path('users/', views.user_list, name='user_list'),  # New URL for user list
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/<int:user_id>/', views.dashboard, name='dashboard_user'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('add-item/', views.add_item, name='add_item'),
    path('inventory/', views.view_inventory, name='view_inventory'),
    path('delete-item/<int:item_id>/', views.delete_item, name='delete_item'),
    path('item/<int:item_id>/', views.view_item_details, name='view_item_details'),
    path('order-item/<int:item_id>/', views.order_item, name='order_item'),
    path('orders/', views.myorders, name='view_orders'),
    path('assignorders/',views.assignorder,name='assignorders'),
    path('delivery/', views.deliveryboy, name='deliver_orders')
]