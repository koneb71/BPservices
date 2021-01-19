from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from app.views import common, sales

urlpatterns = [
    path('', common.index, name="index"),
    path('sales', sales.index, name="sales"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)