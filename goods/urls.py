from django.urls import path
from . import views

app_name = 'goods'

urlpatterns = [
    path('', views.catalog, name='catalog'),  # главная страница будет каталогом
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
]