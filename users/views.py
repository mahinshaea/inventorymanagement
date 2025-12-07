import os
from django.utils import timezone
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator
from .models import item, order, user, role_choices
from django.shortcuts import get_object_or_404
from django.conf import settings
import google.generativeai as genai
from django.views.decorators.http import require_http_methods
import logging

logger = logging.getLogger(__name__)
from rest_framework import viewsets, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from .serializers import UserSerializer, ItemSerializer, OrderSerializer
from .forms import  orderform
genai.configure(api_key="AIzaSyA_tct7JllcC_qJzZASx6yQfD5C-RnJY20")

def printhello(request):
    return render(request, 'hello.html', { 'name': 'Django User' })

def register(request):
    """Handle user registration with role selection."""
    if request.method == 'POST':
        try:
            username = request.POST.get('name')
            password = request.POST.get('password')
            email = request.POST.get('email')
            role = request.POST.get('role', 'customer')  # Get role from form, default to customer

            # Validate role is one of allowed choices
            valid_roles = [choice[0] for choice in role_choices]
            if role not in valid_roles:
                role = 'customer'  # Default if invalid role submitted

            # Check if user already exists
            if user.objects.filter(email=email).exists():
                messages.error(request, 'Email already registered')
                return render(request, 'register.html', {
                    'name': username,
                    'email': email,
                    'role': role,
                    'roles': role_choices,
                })

            # Create new user with selected role
            new_user = user(
                name=username,
                password=password,  # In production, use password hashing
                email=email,
                role=role
            )
            new_user.save()

            messages.success(request, 'Registration successful! Please log in.')
            return redirect('login')

        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
            return render(request, 'register.html', {
                'name': username,
                'email': email,
                'role': role,
                'roles': role_choices,
            })

    return render(request, 'register.html', {'roles': role_choices})



def user_list(request):
    """Display list of all registered users."""
    users = user.objects.all().order_by('-created_at')
    return render(request, 'user_list.html', {'users': users})


def dashboard(request, user_id=None):
    """Role-based dashboard with Gemini AI ingredient extraction and inventory check."""
    # 1️⃣ Identify logged-in user
    if user_id is None:
        session_user_id = request.session.get('user_id')
        if session_user_id:
            u = get_object_or_404(user, pk=session_user_id)
        else:
            messages.error(request, 'Please log in first')
            return redirect('login')
    else:
        u = get_object_or_404(user, pk=user_id)

    # 2️⃣ Role-based template
    role = (u.role or '').lower()
    template_map = {
        'admin': 'admin_dashboard.html',
        'manager': 'manager_dashboard.html',
        'customer': 'customer_dashboard.html',
        'deliveryboy': 'delivery_dashboard.html',
    }

    # 3️⃣ Normal item search
    search_query = request.GET.get('search', '')
    items = item.objects.filter(quantity__gt=0, expirydate__gt=timezone.now())
    if search_query:
        items = items.filter(name__icontains=search_query)

    # 4️⃣ AI Recipe Search
    ai_recipe = request.GET.get('ai_recipe', '')
    ingredient_list, available_ingredients, missing_ingredients = [], [], []

    if ai_recipe:
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            prompt = f"List the main ingredients required to make {ai_recipe}. Respond only with ingredient names separated by commas."
            response = model.generate_content(prompt)
            raw_text = response.text.strip()
            ingredient_list = [x.strip().lower() for x in raw_text.replace('\n', ',').split(',') if x.strip()]

            # Remove generic words
            common_words = ['water', 'salt', 'sugar', 'oil', 'ghee', 'spices', 'powder', 'mixed vegetables']
            ingredient_list = [i for i in ingredient_list if i not in common_words]

            # Compare with inventory
            inventory_names = list(item.objects.values_list('name', flat=True))
            inventory_names_lower = [name.lower() for name in inventory_names]

            for ing in ingredient_list:
                if any(ing in inv for inv in inventory_names_lower):
                    available_ingredients.append(ing)
                else:
                    missing_ingredients.append(ing)

            # Filter items to only show available ones
            items = items.filter(name__in=[i for i in inventory_names if any(ing in i.lower() for ing in available_ingredients)])

        except Exception as e:
            messages.error(request, f"AI error: {str(e)}")

    tpl = template_map.get(role, 'customer_dashboard.html')
    return render(request, tpl, {
        'user': u,
        'items': items,
        'search_query': search_query,
        'ai_recipe': ai_recipe,
        'ingredient_list': ingredient_list,
        'available_ingredients': available_ingredients,
        'missing_ingredients': missing_ingredients,
    })


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Simple login against the custom user model. Sets session['user_id'] on success
    and redirects to the role-based dashboard.
    NOTE: This is a lightweight approach for demo purposes. For production use
    Django's auth system and hashed passwords.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            u = user.objects.get(email=email)
        except user.DoesNotExist:
            messages.error(request, 'Invalid credentials')
            return render(request, 'login.html', {'email': email})

        if u.password != password:
            messages.error(request, 'Invalid credentials')
            return render(request, 'login.html', {'email': email})

        # Successful auth: store in session and redirect to dashboard
        request.session['user_id'] = u.id
        # Choose name of URL to redirect to; redirect to per-user dashboard
        return redirect('dashboard_user', user_id=u.id)

    return render(request, 'login.html')


def logout_view(request):
    request.session.pop('user_id', None)
    messages.info(request, 'Logged out')
    return redirect('index')

def add_item(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description')
            price = request.POST.get('price')
            expirydate = request.POST.get('expirydate')
            quantity = request.POST.get('quantity')
            
            # Handle file upload
            if 'image_path' in request.FILES:
                image_file = request.FILES['image_path']
                new_item = item(
                    name=name,
                    description=description,
                    price=price,
                    expirydate=expirydate,
                    quantity=quantity,
                    image_path=image_file
                )
                new_item.save()
                messages.success(request, f'Item "{name}" added successfully!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Please select an image file')
                return render(request, 'add_item.html')
        except Exception as e:
            messages.error(request, f'Error adding item: {str(e)}')
            return render(request, 'add_item.html')
    return render(request, 'add_item.html')
def view_inventory(request):
    """View the current inventory."""
    if request.method == 'GET':
        search_query = request.GET.get('searchInventory', '')
        if search_query:
            inventory_items = item.objects.filter(name__icontains=search_query, quantity__gt=1)
        else:
            inventory_items = item.objects.filter(quantity__gt=1)
    return render(request, 'view_inventory.html', {'inventory_items': inventory_items})
def delete_item(request, item_id):
    """Delete an item from the inventory."""
    if request.method == 'POST':
        try:
            item_to_delete = get_object_or_404(item, pk=item_id)
            item_to_delete.delete()
            messages.success(request, f'Item "{item_to_delete.name}" deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting item: {str(e)}')
    return redirect('view_inventory')
def view_item_details(request, item_id):
    """Show details for a single item.

    The URL provides `item_id`. The template posts to the URL with the id
    so there's no need to read the id from POST data. Use GET/POST both
    but always rely on the URL parameter.
    """
    try:
        item_details = get_object_or_404(item, pk=item_id)
    except Exception:
        messages.error(request, 'Item not found')
        return redirect('dashboard')

    # Existing template file in the project is named 'view_item_detials.html'
    # (note the misspelling). Render that file to avoid TemplateDoesNotExist.
    return render(request, 'view_item_detials.html', {'item': item_details})
def order_item(request, item_id):
    # Require a logged-in custom user stored in session
    session_user_id = request.session.get('user_id')
    if not session_user_id:
        messages.error(request, 'Please log in to place orders')
        return redirect('login')

    customer = get_object_or_404(user, pk=session_user_id)
    product = get_object_or_404(item, pk=item_id)

    if request.method == 'POST':
        form = orderform(request.POST)
        if form.is_valid():
            try:
                order_instance = form.save(commit=False)
                # Attach our custom user and the item
                order_instance.user = customer
                order_instance.item = product
                order_instance.total_price = order_instance.item.price * order_instance.quantity
                quantity = order_instance.quantity
                if quantity > product.quantity:
                    raise ValueError('Ordered quantity exceeds available stock')
                item.objects.filter(pk=product.id).update(quantity=product.quantity - quantity)
                order_instance.save()
                messages.success(request, 'Order placed successfully!')
                return redirect('dashboard')
            except Exception as e:
                # Log full traceback to server console and show friendly message
                logger.exception('Error placing order')
                messages.error(request, f'Error placing order: {e}')
                # fall through to re-render form with message
    else:
        form = orderform()

    return render(request, 'order_item.html', {'form': form, 'item': product})
def myorders(request):
    session_user_id = request.session.get('user_id')
    if not session_user_id:
        messages.error(request, 'Please log in to view your orders')
        return redirect('login')

    customer = get_object_or_404(user, pk=session_user_id)
    orders = order.objects.filter(user=customer)

    return render(request, 'my_orders.html', {'orders': orders})
def assignorder(request):
    dboyid = user.objects.filter(role='deliveryboy')  # Fixed model name and role value
    orders = order.objects.filter(status='Pending')
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        delivery_boy_id = request.POST.get('delivery_boy_id')
        try:
            order_instance = get_object_or_404(order, pk=order_id)
            delivery_boy = get_object_or_404(user, pk=delivery_boy_id, role='deliveryboy')
            order_instance.delivery_boy = delivery_boy
            order_instance.status = 'In Progress'
            order_instance.save()
            messages.success(request, f'Order {order_id} assigned to {delivery_boy.name} successfully!')
        except Exception as e:
            messages.error(request, f'Error assigning order: {str(e)}')
    return render(request, 'assign_orders.html', {'orders': orders,'d':dboyid})
def deliveryboy(request):
    session_user_id = request.session.get('user_id')
    if not session_user_id:
        messages.error(request, 'Please log in to view your deliveries')
        return redirect('login')
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        try:
            order_instance = get_object_or_404(order, pk=order_id)
            order_instance.status = 'Completed'
            order_instance.save()
            messages.success(request, f'Order {order_id} marked as completed!')
        except Exception as e:
            messages.error(request, f'Error marking order as completed: {str(e)}')
    delivery_boy = get_object_or_404(user, pk=session_user_id, role='deliveryboy')
    deliveries = order.objects.filter(delivery_boy=delivery_boy, status='In Progress')
    return render(request, 'deliver_orders.html', {'deliveries': deliveries})


# --- API ViewSets using Django REST Framework ---


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows users to be viewed (Read-only for security).
    Access should be restricted (e.g., to Admins).
    """
    queryset = user.objects.all().order_by('-created_at')
    serializer_class = UserSerializer
    # In a real app, you would define custom permissions to check role='admin'
    # For now, we use DRF's built-in IsAdminUser as a placeholder for high-level access.
    permission_classes = [IsAdminUser]


class ItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and managing inventory items.
    """
    queryset = item.objects.all().order_by('-created_at')
    serializer_class = ItemSerializer
    
    # Restrict creation, update, and deletion to authenticated staff
    def get_permissions(self):
        # Allow anonymous read-only access (GET/HEAD/OPTIONS), require admin for writes
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            self.permission_classes = [AllowAny]
        else:
            self.permission_classes = [IsAdminUser]
        return [permission() for permission in self.permission_classes]
    
    # Override queryset to only show available items (for customer-facing API)
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter logic similar to your existing dashboard view
        return queryset.filter(quantity__gt=0, expirydate__gt=timezone.now())


class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and creating customer orders.
    """
    queryset = order.objects.all().order_by('-order_date')
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    # Custom logic to handle order creation
    def perform_create(self, serializer):
        # The existing order_item view has complex logic:
        # 1. Attaching the customer user
        # 2. Calculating total_price
        # 3. Deducting stock (item.quantity)
        
        # We must manually replicate this logic here or within the serializer's create method.
        # This implementation requires the 'item' field to be sent in the POST data.
        
        ordered_item = serializer.validated_data.get('item')
        quantity = serializer.validated_data.get('quantity')
        
        if ordered_item is None or quantity is None:
            raise serializers.ValidationError({"detail": "`item` and `quantity` are required."})
        
        if quantity > ordered_item.quantity:
            raise serializers.ValidationError({"quantity": "Ordered quantity exceeds available stock."})
            
        # Deduct stock
        ordered_item.quantity -= quantity
        ordered_item.save()
        
        # Calculate price and save the order
        total_price = ordered_item.price * quantity
        
        # This requires the authenticated user from the request
        # NOTE: This assumes you have proper DRF authentication configured!
        serializer.save(user=self.request.user, total_price=total_price)


class APILogin(APIView):
    """Simple API login endpoint that sets the session['user_id'] for subsequent requests.

    POST payload: {"email": "...", "password": "..."}
    Returns JSON with user info on success and sets the session cookie.
    """
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({"detail": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            u = user.objects.get(email=email)
        except user.DoesNotExist:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)

        if u.password != password:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)

        # Set session marker used by the site views
        request.session['user_id'] = u.id

        return Response({
            "success": True,
            "user": {"id": u.id, "name": u.name, "email": u.email, "role": u.role}
        })


class APILogout(APIView):
    """Simple API logout endpoint that removes the session marker."""
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        request.session.pop('user_id', None)
        return Response({"success": True})
def test_gemini(request):
    import google.generativeai as genai
    import os



    model = genai.GenerativeModel("gemini-2.5-flash")

    try:
        prompt = "List 5 ingredients needed to make sambar."
        response = model.generate_content(prompt)
        print("Gemini raw response:", response)
        print("Gemini text:", getattr(response, "text", None))
        return HttpResponse(f"<pre>{getattr(response, 'text', None)}</pre>")
    except Exception as e:
        return HttpResponse(f"<pre>Error: {e}</pre>")
