# apps/market/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ProductViewSet, OrderViewSet, ValuationAPI

router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="product")
router.register(r"orders", OrderViewSet, basename="order")

urlpatterns = [
    path("valuation/", ValuationAPI.as_view(), name="valuation"),
    path("", include(router.urls)),
]