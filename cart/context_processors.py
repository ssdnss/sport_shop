from .views import get_cart

def cart_count(request):
    cart = get_cart(request)
    total_items = sum(item.quantity for item in cart.items.all())
    return {'cart_total_items': total_items}