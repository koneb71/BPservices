from django.contrib import admin

from app.models import Item, Supplier, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    pass


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    pass