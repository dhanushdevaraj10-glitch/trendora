import json
import os
import tempfile
from io import BytesIO
from urllib.parse import parse_qs, urlsplit

from django.contrib.auth import get_user_model
from django.core.files.storage import storages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Cart, Category, Favourite, Product, getFileName


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

    def test_category_image_can_be_uploaded_in_admin(self):
        image_data = BytesIO()
        Image.new('RGB', (1, 1), color='red').save(image_data, format='PNG')

        with tempfile.TemporaryDirectory() as media_root, override_settings(
            MEDIA_ROOT=media_root,
            STORAGES={
                'default': {
                    'BACKEND': 'django.core.files.storage.FileSystemStorage',
                },
                'staticfiles': {
                    'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
                },
            },
        ):
            response = self.client.post(
                reverse('admin:shop_category_add'),
                {
                    'name': 'Phones with image',
                    'description': 'Mobile phones',
                    'image': SimpleUploadedFile(
                        'phones.png',
                        image_data.getvalue(),
                        content_type='image/png',
                    ),
                },
            )

            self.assertEqual(response.status_code, 302)
            category = Category.objects.get(name='Phones with image')
            self.assertTrue(category.image.name)
            self.assertTrue(category.image.storage.exists(category.image.name))

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
    def test_authenticated_navigation_shows_username_and_logout(self):
        user = get_user_model().objects.create_user(
            username='customer',
            password='correct-password',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('home'))

        self.assertContains(response, 'customer')
        self.assertContains(response, 'Logout')
        self.assertNotContains(response, '>Login</a>')

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

    def test_login_returns_user_to_requested_page(self):
        get_user_model().objects.create_user(
            username='customer',
            password='correct-password',
        )

        response = self.client.post(
            reverse('login') + '?next=' + reverse('cart'),
            {
                'username': 'customer',
                'password': 'correct-password',
                'next': reverse('cart'),
            },
        )

        self.assertRedirects(response, reverse('cart'))

    def test_cart_and_favorites_redirect_guests_to_register(self):
        for page_name in ('cart', 'favViewPage'):
            response = self.client.get(reverse(page_name))

            self.assertEqual(response.status_code, 302)
            self.assertEqual(urlsplit(response.url).path, reverse('register'))
            self.assertEqual(
                parse_qs(urlsplit(response.url).query),
                {'next': [reverse(page_name)]},
            )

    def test_authenticated_user_can_open_cart_and_favorites(self):
        user = get_user_model().objects.create_user(
            username='customer',
            password='correct-password',
        )
        self.client.force_login(user)

        for page_name in ('cart', 'favViewPage'):
            response = self.client.get(reverse(page_name))

            self.assertEqual(response.status_code, 200)

    def test_register_preserves_requested_page_for_login(self):
        response = self.client.post(
            reverse('register') + '?next=' + reverse('cart'),
            {
                'username': 'new-customer',
                'email': 'new-customer@example.com',
                'password1': 'Safe-password-123!',
                'password2': 'Safe-password-123!',
                'next': reverse('cart'),
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlsplit(response.url).path, reverse('login'))
        self.assertEqual(
            parse_qs(urlsplit(response.url).query),
            {'next': [reverse('cart')]},
        )


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


class ProductSearchTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Phones',
            description='Mobile phones',
        )
        self.product = Product.objects.create(
            category=self.category,
            name='Example Smartphone',
            vendor='Example Brand',
            Quantity=5,
            original_price='100.00',
            Selling_price='90.00',
            description='A sample device',
        )

    def test_search_finds_active_products_by_name(self):
        response = self.client.get(reverse('search'), {'q': 'smartphone'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)

    def test_search_matches_category_and_excludes_hidden_products(self):
        hidden_product = Product.objects.create(
            category=self.category,
            name='Hidden Phone',
            vendor='Hidden Brand',
            Quantity=1,
            original_price='100.00',
            Selling_price='90.00',
            description='Hidden from the catalog',
            status=True,
        )

        response = self.client.get(reverse('search'), {'q': 'phones'})

        self.assertContains(response, self.product.name)
        self.assertNotContains(response, hidden_product.name)

    def test_search_shows_prompt_until_a_query_is_submitted(self):
        response = self.client.get(reverse('search'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enter a product name, brand, or category')
        self.assertNotContains(response, self.product.name)


class GuestShoppingTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='customer',
            password='correct-password',
        )
        self.category = Category.objects.create(
            name='Phones',
            description='Mobile phones',
        )
        self.product = Product.objects.create(
            category=self.category,
            name='Example Smartphone',
            vendor='Example Brand',
            Quantity=8,
            original_price='100.00',
            Selling_price='90.00',
            description='A sample device',
        )

    def post_product_action(self, url_name, payload):
        return self.client.post(
            reverse(url_name),
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

    def test_guest_product_actions_require_login(self):
        cart_response = self.post_product_action(
            'addtocart',
            {'pid': self.product.id, 'product_qty': 2},
        )
        self.assertEqual(cart_response.status_code, 401)
        self.assertEqual(
            cart_response.json()['status'],
            'Please log in to add this item to your cart.',
        )

        favorite_response = self.post_product_action(
            'fav',
            {'pid': self.product.id},
        )
        self.assertEqual(favorite_response.status_code, 401)
        self.assertEqual(
            favorite_response.json()['status'],
            'Please log in to add this item to your favorites.',
        )
        self.assertFalse(Cart.objects.exists())
        self.assertFalse(Favourite.objects.exists())
        self.assertNotIn('guest_cart', self.client.session)
        self.assertNotIn('guest_favorites', self.client.session)

    def test_authenticated_user_can_add_cart_and_favorite_items(self):
        self.client.force_login(self.user)

        cart_response = self.post_product_action(
            'addtocart',
            {'pid': self.product.id, 'product_qty': 2},
        )
        favorite_response = self.post_product_action(
            'fav',
            {'pid': self.product.id},
        )

        self.assertEqual(cart_response.json()['status'], 'Product Added to Cart')
        self.assertEqual(favorite_response.json()['status'], 'Product Added to Favourite')
        self.assertTrue(Cart.objects.filter(User=self.user, Products=self.product).exists())
        self.assertTrue(
            Favourite.objects.filter(User=self.user, Product=self.product).exists()
        )

    def test_guest_items_merge_into_account_on_login(self):
        session = self.client.session
        session['guest_cart'] = {str(self.product.id): 3}
        session['guest_favorites'] = [self.product.id]
        session.save()
        Cart.objects.create(
            User=self.user,
            Products=self.product,
            Product_qty=4,
        )

        response = self.client.post(
            reverse('login'),
            {'username': 'customer', 'password': 'correct-password'},
        )

        self.assertRedirects(response, reverse('home'))
        self.assertEqual(
            Cart.objects.get(User=self.user, Products=self.product).Product_qty,
            7,
        )
        self.assertEqual(
            Favourite.objects.filter(User=self.user, Product=self.product).count(),
            1,
        )
        self.assertNotIn('guest_cart', self.client.session)
        self.assertNotIn('guest_favorites', self.client.session)
