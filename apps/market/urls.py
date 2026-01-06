# apps/market/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ProductViewSet, OrderViewSet, ValuationAPI, CategoryViewSet, DeviceModelViewSet, BrandViewSet
from .views_listing import (
    DraftInitAPI, DraftUploadImagesAPI, DraftAnalyzeAPI, DraftEstimateAPI, DraftPublishAPI
)

router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="product")
router.register(r"orders", OrderViewSet, basename="order")
router.register(r"categories", CategoryViewSet, basename="market-category")
router.register(r"device-models", DeviceModelViewSet, basename="market-device-model")
router.register(r"brands", BrandViewSet, basename="market-brand")

urlpatterns = [
    path("valuation/", ValuationAPI.as_view(), name="valuation"),
    path("device-models/reference/", DeviceModelViewSet.as_view({"get": "reference"}), name="device-model-reference"),
    path("", include(router.urls)),
    path("drafts/init/", DraftInitAPI.as_view()),
    path("drafts/<str:draft_key>/images/", DraftUploadImagesAPI.as_view()),
    path("drafts/<str:draft_key>/analyze/", DraftAnalyzeAPI.as_view()),
    path("drafts/<str:draft_key>/estimate/", DraftEstimateAPI.as_view()),
    path("drafts/<str:draft_key>/publish/", DraftPublishAPI.as_view()),
]