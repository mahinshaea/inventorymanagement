from django.urls import path, include
from django.contrib import admin
from rest_framework.routers import DefaultRouter
from . import views

# Initialize the DRF router and register viewsets
router = DefaultRouter()
router.register(r'items', views.ItemViewSet)
router.register(r'orders', views.OrderViewSet)
router.register(r'users', views.UserViewSet)

urlpatterns = [
    # API router endpoints
    path('api/', include(router.urls)),
    # API auth endpoints (login/logout) that set/clear the site's session cookie
    path('api/login/', views.APILogin.as_view(), name='api_login'),
    path('api/logout/', views.APILogout.as_view(), name='api_logout'),

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
    path('delivery/', views.deliveryboy, name='deliver_orders'),
    path('admin/', admin.site.urls),
    path('test-gemini/', views.test_gemini, name='test_gemini'),

]