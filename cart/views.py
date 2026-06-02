from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from goods.models import Product

from .models import Cart, CartItem


def get_cart(request):
    """Получить корзину для текущего пользователя или сессии."""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        cart, created = Cart.objects.get_or_create(session_key=request.session.session_key)
    return cart


def get_cart_total_items(cart):
    return sum(item.quantity for item in cart.items.all())


def cart_detail(request):
    cart = get_cart(request)
    return render(request, 'cart/cart_detail.html', {'cart': cart})


def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id, stock__gt=0)
    cart = get_cart(request)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        if cart_item.quantity >= product.stock:
            total_items = get_cart_total_items(cart)
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': 'На складе нет большего количества этого товара.',
                    'cart_total_items': total_items,
                }, status=400)
            messages.warning(request, "На складе нет большего количества этого товара.")
            return redirect(request.META.get('HTTP_REFERER', 'cart:cart_detail'))
        cart_item.quantity += 1
    cart_item.save()

    total_items = get_cart_total_items(cart)
    if is_ajax:
        return JsonResponse({
            'success': True,
            'message': 'Товар добавлен в корзину.',
            'cart_total_items': total_items,
        })

    messages.success(request, "Товар добавлен в корзину.")
    return redirect(request.META.get('HTTP_REFERER', 'cart:cart_detail'))


def cart_remove(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart=get_cart(request))
    cart_item.delete()
    return redirect('cart:cart_detail')


def cart_update(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart=get_cart(request))
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            cart_item.quantity = min(quantity, cart_item.product.stock)
            cart_item.save()
            if quantity > cart_item.product.stock:
                messages.warning(request, "Количество скорректировано по остатку на складе.")
        else:
            cart_item.delete()
    return redirect('cart:cart_detail')
