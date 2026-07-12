from django.test import TestCase

from .models import Category


class CategoryModelTests(TestCase):
    def test_category_str_returns_name(self):
        category = Category(name='Phones', description='Mobile phones')

        self.assertEqual(str(category), 'Phones')
