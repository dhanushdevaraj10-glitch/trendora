from django.contrib import admin
from .models import *

class CategoryAdmin(admin.ModelAdmin):
    List_display = ('name','image','description')
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product)
