"""
Serializer for the recipe API.
"""
from rest_framework import serializers

from core.models import Recipe

class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for the recipe model."""

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'link']
        read_only_fields = ['id']

class RecipeDetailSerializer(RecipeSerializer):
        """Serializer for the recipe detail view."""

        class Meta(RecipeSerializer.Meta):
            fields = RecipeSerializer.Meta.fields + ['description']