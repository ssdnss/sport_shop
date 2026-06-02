from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ReviewForm
from .models import Category, Product


def catalog(request):
    products_list = Product.objects.all()
    selected_categories = request.GET.getlist('category')
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    in_stock = request.GET.get('in_stock')
    query = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'name')

    if selected_categories:
        products_list = products_list.filter(category__slug__in=selected_categories)

    if min_price:
        products_list = products_list.filter(price__gte=min_price)

    if max_price:
        products_list = products_list.filter(price__lte=max_price)

    if in_stock:
        products_list = products_list.filter(stock__gt=0)

    if query:
        products_list = products_list.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    if sort_by == 'price_asc':
        products_list = products_list.order_by('price')
    elif sort_by == 'price_desc':
        products_list = products_list.order_by('-price')
    elif sort_by == 'name_asc':
        products_list = products_list.order_by('name')
    elif sort_by == 'name_desc':
        products_list = products_list.order_by('-name')
    elif sort_by == 'newest':
        products_list = products_list.order_by('-created_at')
    else:
        products_list = products_list.order_by('name')

    paginator = Paginator(products_list, 12)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    page_query_params = request.GET.copy()
    page_query_params.pop('page', None)
    sort_query_params = request.GET.copy()
    sort_query_params.pop('page', None)
    sort_query_params.pop('sort', None)

    return render(request, 'goods/catalog.html', {
        'products': products,
        'categories': Category.objects.all(),
        'query': query,
        'selected_categories': selected_categories,
        'min_price': min_price,
        'max_price': max_price,
        'in_stock': in_stock,
        'sort_by': sort_by,
        'page_query': page_query_params.urlencode(),
        'sort_query': sort_query_params.urlencode(),
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, stock__gt=0)
    reviews = product.reviews.filter(is_approved=True)

    if request.method == 'POST' and request.user.is_authenticated:
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            return redirect('goods:product_detail', slug=product.slug)
    else:
        form = ReviewForm()

    return render(request, 'goods/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'form': form,
        'avg_rating': product.average_rating(),
        'total_reviews': product.total_reviews(),
    })
