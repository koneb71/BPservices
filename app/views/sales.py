from django.shortcuts import render

from app.models import Item


def index(request):
    items = Item.objects.filter(is_active=True)
    ctx = {
        'title': 'Sales',
        'items': items
    }
    return render(request, 'sales/index.html', ctx)