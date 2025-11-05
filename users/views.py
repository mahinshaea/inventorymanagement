from django.utils import timezone
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator
from .models import item, order, user, role_choices
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
import logging

logger = logging.getLogger(__name__)
from .forms import  orderform


def printhello(request):
    return render(request, 'hello.html', { 'name': 'Django User' })

def register(request):
    """Handle customer registration only."""
    if request.method == 'POST':
        try:
            username = request.POST.get('name')
            password = request.POST.get('password')
            email = request.POST.get('email')

            # Force role to "customer" no matter what is in POST
            role = 'customer'

            # Check if user already exists
            if user.objects.filter(email=email).exists():
                messages.error(request, 'Email already registered')
                return render(request, 'register.html', {
                    'name': username,
                    'email': email,
                })

            # Create new customer user
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
            })

    # No role selection shown since only customers can register
    return render(request, 'register.html')



def user_list(request):
    """Display list of all registered users."""
    users = user.objects.all().order_by('-created_at')
    return render(request, 'user_list.html', {'users': users})


def dashboard(request, user_id=None):
    """Render a role-based dashboard for a user. For now supports passing user_id
    in the URL (e.g. /dashboard/3/) for testing. In a production app you'd use
    authentication and sessions to identify the logged-in user.
    """
    if user_id is None:
        # If no user_id was provided, try to use logged-in user stored in session
        session_user_id = request.session.get('user_id')
        if session_user_id:


            u = get_object_or_404(user, pk=session_user_id)
        else:
            # No user selected or logged in - ask for login / selection
            return render(request, 'dashboard_select.html')

    # If user_id was provided explicitly, override session
    if user_id is not None:
        u = get_object_or_404(user, pk=user_id)

    # Choose template based on role
    role = (u.role or '').lower()
    template_map = {
        'admin': 'admin_dashboard.html',
        'manager': 'manager_dashboard.html',
        'customer': 'customer_dashboard.html',
        'deliveryboy': 'delivery_dashboard.html',
    }
    
    # Handle search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        items = item.objects.filter(name__icontains=search_query, quantity__gt=0, expirydate__gt=timezone.now()).order_by('-created_at')
    else:
        items = item.objects.filter(quantity__gt=0, expirydate__gt=timezone.now()).order_by('-created_at')

    tpl = template_map.get(role, 'customer_dashboard.html')
    return render(request, tpl, {
        'user': u, 
        'items': items,
        'search_query': search_query
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