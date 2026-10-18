import os

from django.contrib.auth import get_user_model
from django.core.files.storage import storages
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Category, Product, getFileName


class CategoryModelTests(TestCase):
    def test_category_str_returns_name(self):
        category = Category(name='Phones', description='Mobile phones')

        self.assertEqual(str(category), 'Phones')


class ShopAdminTests(TestCase):
    def setUp(self):
        admin_user = get_user_model().objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password',
        )
        self.client.force_login(admin_user)

    def test_default_file_storage_is_configured(self):
        self.assertIsNotNone(storages['default'])

    def test_category_can_be_added_in_admin(self):
        response = self.client.post(
            reverse('admin:shop_category_add'),
            {'name': 'Phones', 'description': 'Mobile phones'},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('admin:shop_category_changelist'))
        self.assertTrue(Category.objects.filter(name='Phones').exists())

    def test_product_can_be_added_in_admin(self):
        category = Category.objects.create(
            name='Phones',
            description='Mobile phones',
        )

        response = self.client.post(
            reverse('admin:shop_product_add'),
            {
                'category': category.pk,
                'name': 'Example phone',
                'vendor': 'Example vendor',
                'Quantity': 5,
                'original_price': '100.00',
                'Selling_price': '90.00',
                'description': 'An example product',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('admin:shop_product_changelist'))
        self.assertTrue(Product.objects.filter(name='Example phone').exists())

    def test_upload_filename_is_safe_on_windows(self):
        upload_path = getFileName(None, 'product.png')

        self.assertNotIn(':', upload_path)
        self.assertEqual(os.path.dirname(upload_path), 'uploads')
        self.assertTrue(os.path.basename(upload_path).endswith('_product.png'))


class LoginTests(TestCase):
    def test_login_authenticates_user_with_submitted_password(self):
        user = get_user_model().objects.create_user(
            username='customer',
            password='correct-password',
        )

        response = self.client.post(
            reverse('login'),
            {'username': 'customer', 'password': 'correct-password'},
        )

        self.assertRedirects(response, reverse('home'))
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)


@override_settings(
    STORAGES={
        'default': {
            'BACKEND': 'django.core.files.storage.FileSystemStorage',
        },
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
        },
    }
)
class CollectionNavigationTests(TestCase):
    def test_category_link_uses_category_detail_route(self):
        Category.objects.create(name='Phones', description='Mobile phones')

        response = self.client.get(reverse('collections'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/collections/Phones/"')
