from django.contrib import admin
from .models import Cart, Category, Favourite, Product

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'created_at')


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'Quantity', 'Selling_price', 'status', 'trending')
    list_filter = ('status', 'trending', 'category')


admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Cart)
admin.site.register(Favourite)
