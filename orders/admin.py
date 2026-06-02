from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price', 'get_total')
    can_delete = False
    fields = ('product', 'quantity', 'price', 'get_total')

    def get_total(self, obj):
        return f"{obj.get_total_price()} ₽"
    get_total.short_description = 'Сумма'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_user_info', 'created_at', 'total_price', 'status', 'stock_deducted', 'get_status_badge', 'get_actions_buttons')
    list_filter = ('status', 'stock_deducted', 'created_at')
    search_fields = ('id', 'first_name', 'last_name', 'email', 'phone', 'user__username')
    readonly_fields = ('created_at', 'total_price', 'stock_deducted')
    inlines = [OrderItemInline]
    actions = ['mark_as_paid', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_received', 'mark_as_cancelled']

    fieldsets = (
        ('Информация о заказе', {
            'fields': ('user', 'status', 'created_at', 'total_price', 'stock_deducted'),
        }),
        ('Данные покупателя', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'address'),
        }),
    )

    def get_urls(self):
        custom_urls = [
            path('<int:order_id>/mark_paid/', self.admin_site.admin_view(self.mark_paid_view), name='orders_order_mark_paid'),
            path('<int:order_id>/mark_shipped/', self.admin_site.admin_view(self.mark_shipped_view), name='orders_order_mark_shipped'),
            path('<int:order_id>/mark_received/', self.admin_site.admin_view(self.mark_received_view), name='orders_order_mark_received'),
        ]
        return custom_urls + super().get_urls()

    def get_user_info(self, obj):
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return 'Гость'
    get_user_info.short_description = 'Пользователь'
    get_user_info.admin_order_field = 'user__username'

    def get_status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'paid': 'green',
            'shipped': 'blue',
            'delivered': 'darkgreen',
            'received': 'purple',
            'cancelled': 'red',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display(),
        )
    get_status_badge.short_description = 'Статус'

    def get_actions_buttons(self, obj):
        buttons = []
        if obj.status == 'pending':
            url = reverse('admin:orders_order_mark_paid', args=[obj.id])
            buttons.append(self._button(url, 'Оплачен', 'green'))
        if obj.status in ['pending', 'paid']:
            url = reverse('admin:orders_order_mark_shipped', args=[obj.id])
            buttons.append(self._button(url, 'Отправлен', 'blue'))
        if obj.status in ['shipped', 'delivered']:
            url = reverse('admin:orders_order_mark_received', args=[obj.id])
            buttons.append(self._button(url, 'Получен', 'purple'))
        return format_html(''.join(buttons)) if buttons else '-'
    get_actions_buttons.short_description = 'Действия'

    def _button(self, url, label, color):
        return (
            f'<a class="button" href="{url}" '
            f'style="background: {color}; color: white; padding: 5px 10px; '
            f'text-decoration: none; margin-right: 5px;">{label}</a>'
        )

    def _set_status(self, request, order_id, status, success_message):
        order = self.get_object(request, order_id)
        if order is None:
            self.message_user(request, "Заказ не найден.", level=messages.ERROR)
        else:
            order.status = status
            order.save(update_fields=['status'])
            self.message_user(request, success_message.format(order=order), level=messages.SUCCESS)
        return HttpResponseRedirect(reverse('admin:orders_order_changelist'))

    def mark_paid_view(self, request, order_id):
        return self._set_status(request, order_id, 'paid', "Заказ №{order.id} отмечен как оплаченный.")

    def mark_shipped_view(self, request, order_id):
        return self._set_status(request, order_id, 'shipped', "Заказ №{order.id} отмечен как отправленный.")

    def mark_received_view(self, request, order_id):
        return self._set_status(request, order_id, 'received', "Заказ №{order.id} отмечен как полученный. Остатки на складе обновлены.")

    def mark_as_paid(self, request, queryset):
        for order in queryset:
            order.status = 'paid'
            order.save(update_fields=['status'])
    mark_as_paid.short_description = "Отметить как оплаченные"

    def mark_as_shipped(self, request, queryset):
        for order in queryset:
            order.status = 'shipped'
            order.save(update_fields=['status'])
    mark_as_shipped.short_description = "Отметить как отправленные"

    def mark_as_delivered(self, request, queryset):
        for order in queryset:
            order.status = 'delivered'
            order.save(update_fields=['status'])
    mark_as_delivered.short_description = "Отметить как доставленные"

    def mark_as_received(self, request, queryset):
        for order in queryset:
            order.status = 'received'
            order.save(update_fields=['status'])
    mark_as_received.short_description = "Отметить как полученные и списать товары"

    def mark_as_cancelled(self, request, queryset):
        for order in queryset:
            order.status = 'cancelled'
            order.save(update_fields=['status'])
    mark_as_cancelled.short_description = "Отменить заказы"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price', 'get_total')
    list_filter = ('order__status',)
    search_fields = ('order__id', 'product__name')

    def get_total(self, obj):
        return f"{obj.get_total_price()} ₽"
    get_total.short_description = 'Сумма'
