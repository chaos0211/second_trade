from rest_framework import serializers
from .models import DeviceModel, Product, Order, ValuationOption, ValuationChoice


class ValuationRequestSerializer(serializers.Serializer):
    device_model_id = serializers.IntegerField()
    choice_ids = serializers.ListField(child=serializers.IntegerField())


class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["device_model", "title", "description", "selling_price", "condition_data"]


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"