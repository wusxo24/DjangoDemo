"""
Tests for the recipe API.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)

RECIPES_URL = reverse('recipe:recipe-list')

def detail_url(recipe_id):
    """Create and return a recipe detail URL."""
    return reverse('recipe:recipe-detail', args=[recipe_id])

def create_recipe(user, **params):
    """Create and return a sample recipe."""
    defaults = {
        'title': 'Sample recipe title',
        'time_minutes': 22,
        'price': Decimal('5.25'),
        'description': 'Sample description',
        'link': 'http://example.com/recipe.pdf',
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe
def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)

class PublicRecipeAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(reverse('recipe:recipe-list'))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    class PrivateRecipeAPITests(TestCase):
        """Test authenticated API requests."""

        def setUp(self):
            self.client = APIClient()
            self.user = create_user(email='user@example', password='testpass123')
            self.client.force_authenticate(self.user)

        def test_retrieve_recipes(self):
            """Test retrieving a list of recipes."""
            create_recipe(user=self.user)
            create_recipe(user=self.user)

            res = self.client.get(RECIPES_URL)
            recipes = Recipe.objects.all().order_by('-id')
            serializer = RecipeSerializer(recipes, many=True)
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertEqual(res.data, serializer.data)

        def test_recipe_list_limited_to_user(self):
            """Test list of recipes is limited to authenticated user."""
            other_user = get_user_model().objects.create_user(
                'other@example',
                'otherpass123',
            )
            create_recipe(user=other_user)
            create_recipe(user=self.user)

            res = self.client.get(RECIPES_URL)

            recipes = Recipe.objects.filter(user=self.user)
            serializer = RecipeSerializer(recipes, many=True)
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertEqual(res.data, serializer.data)

        def test_get_recipe_detail(self):
            """Test get recipe detail."""
            recipe = create_recipe(user=self.user)

            url = detail_url(recipe.id)
            res = self.client.get(url)

            serializer = RecipeDetailSerializer(recipe)
            self.assertEqual(res.data, serializer.data)

        def test_create_recipe(self):
            """Test creating a recipe."""
            payload = {
                'title': 'Sample recipe',
                'time_minutes': 30,
                'price': Decimal('5.99'),
            }
            res = self.client.post(RECIPES_URL, payload)

            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            recipe = Recipe.objects.get(id=res.data['id'])
            for k, v in payload.items():
                self.assertEqual(getattr(recipe, k), v)
            self.assertEqual(recipe.user, self.user)

        def test_partial_update(self):
            """Test partial update of a recipe."""
            original_link = 'https://example.com/recipe.pdf'
            recipe = create_recipe(
                user=self.user,
                title='Sample recipe title',
                link=original_link,
            )

            payload = {'title': 'New recipe title'}
            url = detail_url(recipe.id)
            res = self.client.patch(url, payload)

            self.assertEqual(res.status_code, status.HTTP_200_OK)
            recipe.refresh_from_db()
            self.assertEqual(recipe.title, payload['title'])
            self.assertEqual(recipe.link, original_link)
            self.assertEqual(recipe.user, self.user)

        def perform_create(self, serializer):
            serializer.save(user=self.user)