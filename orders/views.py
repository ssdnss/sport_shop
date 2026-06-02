from datetime import timedelta

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, DecimalField, ExpressionWrapper, F, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from cart.views import get_cart

from .forms import OrderCreateForm
from .models import Order, OrderItem


@login_required
def order_create(request):
    cart = get_cart(request)
    if cart.items.count() == 0:
        messages.warning(request, "Ваша корзина пуста, нельзя оформить заказ.")
        return redirect('cart:cart_detail')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.total_price = cart.get_total_price()
            order.save()

            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price,
                )
            cart.items.all().delete()
            messages.success(request, f"Заказ №{order.id} успешно оформлен!")
            return redirect('orders:order_detail', order_id=order.id)
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
            }
        form = OrderCreateForm(initial=initial_data)

    return render(request, 'orders/order_create.html', {'form': form, 'cart': cart})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})


@staff_member_required
def admin_dashboard(request):
    """Административная панель со статистикой."""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    total_orders = Order.objects.count()
    revenue_statuses = ['paid', 'shipped', 'delivered', 'received']
    total_revenue = Order.objects.filter(status__in=revenue_statuses).aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_customers = Order.objects.values('user').distinct().count()
    avg_order_value = Order.objects.aggregate(Avg('total_price'))['total_price__avg'] or 0

    pending_orders = Order.objects.filter(status='pending').count()
    paid_orders = Order.objects.filter(status='paid').count()
    shipped_orders = Order.objects.filter(status='shipped').count()
    delivered_orders = Order.objects.filter(status='delivered').count()
    received_orders = Order.objects.filter(status='received').count()
    cancelled_orders = Order.objects.filter(status='cancelled').count()

    weekly_orders = Order.objects.filter(created_at__date__gte=week_ago).count()
    weekly_revenue = Order.objects.filter(
        created_at__date__gte=week_ago,
        status__in=revenue_statuses,
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0

    monthly_orders = Order.objects.filter(created_at__date__gte=month_ago).count()
    monthly_revenue = Order.objects.filter(
        created_at__date__gte=month_ago,
        status__in=revenue_statuses,
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0

    recent_orders = Order.objects.all().order_by('-created_at')[:10]

    line_total = ExpressionWrapper(
        F('price') * F('quantity'),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    top_products = OrderItem.objects.values('product__name').annotate(
        total_quantity=Sum('quantity'),
        total_sales=Sum(line_total),
    ).order_by('-total_quantity')[:5]

    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_customers': total_customers,
        'avg_order_value': avg_order_value,
        'pending_orders': pending_orders,
        'paid_orders': paid_orders,
        'shipped_orders': shipped_orders,
        'delivered_orders': delivered_orders,
        'received_orders': received_orders,
        'cancelled_orders': cancelled_orders,
        'weekly_orders': weekly_orders,
        'weekly_revenue': weekly_revenue,
        'monthly_orders': monthly_orders,
        'monthly_revenue': monthly_revenue,
        'recent_orders': recent_orders,
        'top_products': top_products,
    }
    return render(request, 'orders/admin_dashboard.html', context)
