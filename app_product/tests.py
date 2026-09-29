from django.test import TestCase

from datetime import timedelta

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APITestCase

from app_auth.models import User
from app_product.models import (
    Category, Product, ProductColor, ProductSize, ProductMaterial,
    ProductOption, ProductImage, Discount, DiscountCode,
)


class BaseAPITestCase(APITestCase):
    """
    این کلاس پایه است. هر کلاس تست دیگه از این ارث‌بری می‌کنه
    تا مجبور نباشیم هر بار از اول یه کاربر و یه محصول بسازیم.
    """

    def setUp(self):
        # جلوگیری از خطای 429 (rate limit) بین تست‌ها
        cache.clear()

        self.user = User.objects.create_user(
            phone_number='09120000001', password='User12345',
            username='normal_user', is_phone_verified=True,
        )
        self.admin = User.objects.create_user(
            phone_number='09120000002', password='Admin12345',
            username='admin_user', role='admin', is_staff=True,
            is_phone_verified=True,
        )

        self.category = Category.objects.create(
            name='Men', description='Men clothing', is_active=True
        )
        self.product = Product.objects.create(
            category=self.category, name='T-Shirt', description='Cotton',
            brand='Nike', gender='men', is_active=True,
        )


class CategoryAPITests(BaseAPITestCase):
    base = '/api/product/categories/'

    def test_list_returns_only_active_categories(self):
        Category.objects.create(name='Hidden', description='x', is_active=False)
        response = self.client.get(self.base)
        self.assertEqual(response.status_code, 200)
        names = [c['name'] for c in response.data['category_list']]
        self.assertIn('Men', names)
        self.assertNotIn('Hidden', names)

    def test_list_filter_by_parent(self):
        sub = Category.objects.create(
            parent=self.category, name='Shirts', description='x', is_active=True
        )
        response = self.client.get(f'{self.base}?parent={self.category.id}')
        ids = [c['id'] for c in response.data['category_list']]
        self.assertEqual(ids, [sub.id])

    def test_list_filter_root_categories(self):
        Category.objects.create(
            parent=self.category, name='Shirts', description='x', is_active=True
        )
        response = self.client.get(f'{self.base}?parent=null')
        ids = [c['id'] for c in response.data['category_list']]
        self.assertEqual(ids, [self.category.id])

    def test_detail_success(self):
        response = self.client.get(f'{self.base}{self.category.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'Men')

    def test_detail_not_found_for_inactive(self):
        hidden = Category.objects.create(name='Hidden', description='x', is_active=False)
        response = self.client.get(f'{self.base}{hidden.id}/')
        self.assertEqual(response.status_code, 404)

    def test_create_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(f'{self.base}create/', {
            'name': 'Women', 'description': 'Women clothing', 'is_active': True,
        })
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Category.objects.filter(name='Women').exists())

    def test_create_forbidden_for_normal_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'{self.base}create/', {
            'name': 'Women', 'description': 'x', 'is_active': True,
        })
        self.assertEqual(response.status_code, 403)

    def test_create_requires_login(self):
        response = self.client.post(f'{self.base}create/', {
            'name': 'Women', 'description': 'x', 'is_active': True,
        })
        self.assertIn(response.status_code, (401, 403))

    def test_update_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.put(f'{self.base}{self.category.id}/update/', {
            'name': 'Men Updated', 'description': 'New', 'is_active': True,
        })
        self.assertEqual(response.status_code, 200)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, 'Men Updated')

    def test_update_forbidden_for_normal_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.put(f'{self.base}{self.category.id}/update/', {
            'name': 'Hacked', 'description': 'x', 'is_active': True,
        })
        self.assertEqual(response.status_code, 403)

    def test_delete_as_admin(self):
        empty = Category.objects.create(name='Empty', description='x', is_active=True)
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f'{self.base}{empty.id}/delete/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Category.objects.filter(id=empty.id).exists())

    def test_delete_forbidden_for_normal_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'{self.base}{self.category.id}/delete/')
        self.assertEqual(response.status_code, 403)


class ProductAPITests(BaseAPITestCase):
    base = '/api/product/products/'

    def test_list_success_and_pagination_fields(self):
        response = self.client.get(self.base)
        self.assertEqual(response.status_code, 200)
        for key in ('count', 'total_pages', 'current_page', 'products'):
            self.assertIn(key, response.data)

    def test_list_hides_inactive_products(self):
        Product.objects.create(
            category=self.category, name='Hidden', description='x', is_active=False
        )
        response = self.client.get(self.base)
        names = [p['name'] for p in response.data['products']]
        self.assertNotIn('Hidden', names)

    def test_list_filter_by_brand(self):
        Product.objects.create(
            category=self.category, name='Shoes', description='x',
            brand='Adidas', is_active=True,
        )
        response = self.client.get(f'{self.base}?brand=adidas')
        names = [p['name'] for p in response.data['products']]
        self.assertEqual(names, ['Shoes'])

    def test_list_search_by_name(self):
        response = self.client.get(f'{self.base}?search=shirt')
        names = [p['name'] for p in response.data['products']]
        self.assertEqual(names, ['T-Shirt'])

    def test_list_filter_by_category(self):
        other = Category.objects.create(name='Other', description='x', is_active=True)
        Product.objects.create(category=other, name='Other Item', description='x', is_active=True)
        response = self.client.get(f'{self.base}?category={other.id}')
        names = [p['name'] for p in response.data['products']]
        self.assertEqual(names, ['Other Item'])

    def test_detail_success(self):
        response = self.client.get(f'{self.base}{self.product.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'T-Shirt')
        self.assertIn('options', response.data)
        self.assertIn('images', response.data)

    def test_detail_not_found_for_inactive(self):
        hidden = Product.objects.create(
            category=self.category, name='Hidden', description='x', is_active=False
        )
        response = self.client.get(f'{self.base}{hidden.id}/')
        self.assertEqual(response.status_code, 404)

    def test_related_excludes_itself(self):
        sibling = Product.objects.create(
            category=self.category, name='Pants', description='x', is_active=True
        )
        response = self.client.get(f'{self.base}{self.product.id}/related/')
        self.assertEqual(response.status_code, 200)
        ids = [p['id'] for p in response.data['related_products']]
        self.assertIn(sibling.id, ids)
        self.assertNotIn(self.product.id, ids)

    def test_create_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(f'{self.base}create/', {
            'category': self.category.id, 'name': 'Jacket',
            'description': 'Warm', 'brand': 'Zara', 'gender': 'men',
            'is_active': True,
        })
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Product.objects.filter(name='Jacket').exists())

    def test_create_forbidden_for_normal_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'{self.base}create/', {
            'category': self.category.id, 'name': 'Jacket',
            'description': 'x', 'is_active': True,
        })
        self.assertEqual(response.status_code, 403)

    def test_create_invalid_data(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(f'{self.base}create/', {'name': 'No category'})
        self.assertEqual(response.status_code, 400)

    def test_update_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.put(f'{self.base}{self.product.id}/update/', {
            'category': self.category.id, 'name': 'T-Shirt v2',
            'description': 'Cotton', 'brand': 'Nike', 'gender': 'men',
            'is_active': True,
        })
        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'T-Shirt v2')

    def test_change_status_toggles(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(f'{self.base}{self.product.id}/change-status/')
        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.assertFalse(self.product.is_active)

    def test_change_status_forbidden_for_normal_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(f'{self.base}{self.product.id}/change-status/')
        self.assertEqual(response.status_code, 403)

    def test_delete_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f'{self.base}{self.product.id}/delete/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Product.objects.filter(id=self.product.id).exists())

    def test_delete_forbidden_for_normal_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'{self.base}{self.product.id}/delete/')
        self.assertEqual(response.status_code, 403)


class ProductAttributesAPITests(BaseAPITestCase):
    """تست‌های Color، Size، Material — این‌ها مستقل و قابل استفاده مجدد هستن."""

    def test_create_color_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/product/colors/create/', {
            'name': 'Red', 'color_code': '#FF0000',
        })
        self.assertEqual(response.status_code, 201)
        self.assertTrue(ProductColor.objects.filter(name='Red').exists())

    def test_create_color_forbidden_for_normal_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/product/colors/create/', {
            'name': 'Red', 'color_code': '#FF0000',
        })
        self.assertEqual(response.status_code, 403)

    def test_update_color(self):
        color = ProductColor.objects.create(name='Blue', color_code='#0000FF')
        self.client.force_authenticate(user=self.admin)
        response = self.client.put(f'/api/product/colors/{color.id}/update/', {
            'name': 'Navy Blue', 'color_code': '#000080',
        })
        self.assertEqual(response.status_code, 200)
        color.refresh_from_db()
        self.assertEqual(color.name, 'Navy Blue')

    def test_delete_color(self):
        color = ProductColor.objects.create(name='Green', color_code='#00FF00')
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f'/api/product/colors/{color.id}/delete/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(ProductColor.objects.filter(id=color.id).exists())

    def test_create_size_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/product/sizes/create/', {'name': 'XL'})
        self.assertEqual(response.status_code, 201)
        self.assertTrue(ProductSize.objects.filter(name='XL').exists())

    def test_create_material_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/product/materials/create/', {
            'name': 'Cotton', 'description': '100% cotton',
        })
        self.assertEqual(response.status_code, 201)
        self.assertTrue(ProductMaterial.objects.filter(name='Cotton').exists())

    def test_delete_material_forbidden_for_normal_user(self):
        material = ProductMaterial.objects.create(name='Wool', description='x')
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/product/materials/{material.id}/delete/')
        self.assertEqual(response.status_code, 403)


class ProductOptionAPITests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.color = ProductColor.objects.create(name='Red', color_code='#FF0000')
        self.size = ProductSize.objects.create(name='M')
        self.material = ProductMaterial.objects.create(name='Cotton', description='x')

    def _payload(self, **overrides):
        data = {
            'product': self.product.id,
            'color': self.color.id,
            'size': self.size.id,
            'material': self.material.id,
            'retail_price': 500000,
            'wholesale_price': 400000,
            'wholesale_min_quantity': 10,
            'stock': 20,
        }
        data.update(overrides)
        return data

    def test_create_option_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/product/products/options/create/', self._payload())
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ProductOption.objects.count(), 1)

    def test_create_option_forbidden_for_normal_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/product/products/options/create/', self._payload())
        self.assertEqual(response.status_code, 403)

    def test_create_duplicate_combination_rejected(self):
        self.client.force_authenticate(user=self.admin)
        first = self.client.post('/api/product/products/options/create/', self._payload())
        self.assertEqual(first.status_code, 201)

        second = self.client.post('/api/product/products/options/create/', self._payload())
        self.assertEqual(second.status_code, 400)
        self.assertEqual(ProductOption.objects.count(), 1)

    def test_different_size_same_product_is_allowed(self):
        other_size = ProductSize.objects.create(name='L')
        self.client.force_authenticate(user=self.admin)
        self.client.post('/api/product/products/options/create/', self._payload())
        response = self.client.post(
            '/api/product/products/options/create/',
            self._payload(size=other_size.id)
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ProductOption.objects.count(), 2)

    def test_update_stock_only(self):
        option = ProductOption.objects.create(
            product=self.product, color=self.color, size=self.size, material=self.material,
            retail_price=500000, wholesale_price=400000, wholesale_min_quantity=10, stock=5,
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f'/api/product/products/options/{option.id}/update-stock/', {'stock': 50}
        )
        self.assertEqual(response.status_code, 200)
        option.refresh_from_db()
        self.assertEqual(option.stock, 50)
        self.assertEqual(option.retail_price, 500000)

    def test_update_stock_missing_field(self):
        option = ProductOption.objects.create(
            product=self.product, color=self.color, size=self.size, material=self.material,
            retail_price=500000, wholesale_price=400000, wholesale_min_quantity=10, stock=5,
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(f'/api/product/products/options/{option.id}/update-stock/', {})
        self.assertEqual(response.status_code, 400)

    def test_update_price_partial(self):
        option = ProductOption.objects.create(
            product=self.product, color=self.color, size=self.size, material=self.material,
            retail_price=500000, wholesale_price=400000, wholesale_min_quantity=10, stock=5,
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f'/api/product/products/options/{option.id}/update-price/',
            {'retail_price': 600000}
        )
        self.assertEqual(response.status_code, 200)
        option.refresh_from_db()
        self.assertEqual(option.retail_price, 600000)
        self.assertEqual(option.wholesale_price, 400000)

    def test_update_price_no_fields_rejected(self):
        option = ProductOption.objects.create(
            product=self.product, color=self.color, size=self.size, material=self.material,
            retail_price=500000, wholesale_price=400000, wholesale_min_quantity=10, stock=5,
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(f'/api/product/products/options/{option.id}/update-price/', {})
        self.assertEqual(response.status_code, 400)

    def test_delete_option_as_admin(self):
        option = ProductOption.objects.create(
            product=self.product, color=self.color, size=self.size, material=self.material,
            retail_price=500000, wholesale_price=400000, wholesale_min_quantity=10, stock=5,
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f'/api/product/products/options/{option.id}/delete/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(ProductOption.objects.filter(id=option.id).exists())

    def test_option_appears_in_product_detail(self):
        ProductOption.objects.create(
            product=self.product, color=self.color, size=self.size, material=self.material,
            retail_price=500000, wholesale_price=400000, wholesale_min_quantity=10, stock=5,
        )
        response = self.client.get(f'/api/product/products/{self.product.id}/')
        self.assertEqual(len(response.data['options']), 1)
        self.assertEqual(response.data['options'][0]['color']['name'], 'Red')


class ProductImageAPITests(BaseAPITestCase):
    def test_create_image_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        fake_image = SimpleUploadedFile('test.jpg', b'file_content', content_type='image/jpeg')
        response = self.client.post('/api/product/products/images/create/', {
            'product': self.product.id, 'image': fake_image, 'is_primary': True,
        }, format='multipart')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ProductImage.objects.count(), 1)

    def test_delete_image_forbidden_for_normal_user(self):
        image = ProductImage.objects.create(product=self.product, is_primary=False)
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/product/products/images/{image.id}/delete/')
        self.assertEqual(response.status_code, 403)


class DiscountAPITests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.color = ProductColor.objects.create(name='Red', color_code='#FF0000')
        self.size = ProductSize.objects.create(name='M')
        self.material = ProductMaterial.objects.create(name='Cotton', description='x')
        self.option = ProductOption.objects.create(
            product=self.product, color=self.color, size=self.size, material=self.material,
            retail_price=500000, wholesale_price=400000, wholesale_min_quantity=10, stock=10,
        )

    def test_create_discount_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        now = timezone.now()
        response = self.client.post('/api/product/discounts/create/', {
            'option': self.option.id,
            'type': 'percentage',
            'value': 20,
            'start_at': now.isoformat(),
            'end_at': (now + timedelta(days=7)).isoformat(),
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Discount.objects.count(), 1)

    def test_create_discount_forbidden_for_normal_user(self):
        self.client.force_authenticate(user=self.user)
        now = timezone.now()
        response = self.client.post('/api/product/discounts/create/', {
            'option': self.option.id, 'type': 'fixed', 'value': 50000,
            'start_at': now.isoformat(), 'end_at': (now + timedelta(days=1)).isoformat(),
        })
        self.assertEqual(response.status_code, 403)

    def test_active_discount_shown_in_option_detail(self):
        now = timezone.now()
        Discount.objects.create(
            option=self.option, type='percentage', value=20,
            start_at=now - timedelta(days=1), end_at=now + timedelta(days=1),
        )
        response = self.client.get(f'/api/product/products/{self.product.id}/')
        option_data = response.data['options'][0]
        self.assertIsNotNone(option_data['active_discount'])

    def test_expired_discount_not_shown(self):
        now = timezone.now()
        Discount.objects.create(
            option=self.option, type='percentage', value=20,
            start_at=now - timedelta(days=10), end_at=now - timedelta(days=1),
        )
        response = self.client.get(f'/api/product/products/{self.product.id}/')
        option_data = response.data['options'][0]
        self.assertIsNone(option_data['active_discount'])

    def test_future_discount_not_shown(self):
        now = timezone.now()
        Discount.objects.create(
            option=self.option, type='percentage', value=20,
            start_at=now + timedelta(days=1), end_at=now + timedelta(days=10),
        )
        response = self.client.get(f'/api/product/products/{self.product.id}/')
        option_data = response.data['options'][0]
        self.assertIsNone(option_data['active_discount'])

    def test_discounted_products_list_only_shows_active_discounts(self):
        now = timezone.now()
        Discount.objects.create(
            option=self.option, type='percentage', value=20,
            start_at=now - timedelta(days=1), end_at=now + timedelta(days=1),
        )
        other_product = Product.objects.create(
            category=self.category, name='No Discount', description='x', is_active=True
        )
        response = self.client.get('/api/product/discounts/products/')
        ids = [p['id'] for p in response.data['discount_products']]
        self.assertIn(self.product.id, ids)
        self.assertNotIn(other_product.id, ids)

    def test_delete_discount_as_admin(self):
        now = timezone.now()
        discount = Discount.objects.create(
            option=self.option, type='fixed', value=50000,
            start_at=now, end_at=now + timedelta(days=1),
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f'/api/product/discounts/{discount.id}/delete/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Discount.objects.filter(id=discount.id).exists())


class DiscountCodeAPITests(BaseAPITestCase):
    def test_create_code_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        now = timezone.now()
        response = self.client.post('/api/product/discount-codes/create/', {
            'code': 'SUMMER20', 'type': 'percentage', 'value': 20,
            'start_at': now.isoformat(), 'end_at': (now + timedelta(days=30)).isoformat(),
        })
        self.assertEqual(response.status_code, 201)
        self.assertTrue(DiscountCode.objects.filter(code='SUMMER20').exists())

    def test_create_code_forbidden_for_normal_user(self):
        self.client.force_authenticate(user=self.user)
        now = timezone.now()
        response = self.client.post('/api/product/discount-codes/create/', {
            'code': 'HACK10', 'type': 'fixed', 'value': 10000,
            'start_at': now.isoformat(), 'end_at': (now + timedelta(days=1)).isoformat(),
        })
        self.assertEqual(response.status_code, 403)

    def test_apply_valid_code_success(self):
        now = timezone.now()
        code = DiscountCode.objects.create(
            code='WELCOME10', type='percentage', value=10,
            start_at=now - timedelta(hours=1), end_at=now + timedelta(days=1),
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/auth/discount-codes/apply/', {'code': 'WELCOME10'})
        self.assertEqual(response.status_code, 200)
        code.refresh_from_db()
        self.assertTrue(code.is_used)
        self.assertEqual(code.used_by, self.user)

    def test_apply_code_requires_login(self):
        now = timezone.now()
        DiscountCode.objects.create(
            code='NEEDLOGIN', type='fixed', value=10000,
            start_at=now, end_at=now + timedelta(days=1),
        )
        response = self.client.post('/api/auth/discount-codes/apply/', {'code': 'NEEDLOGIN'})
        self.assertIn(response.status_code, (401, 403))

    def test_apply_already_used_code_rejected(self):
        now = timezone.now()
        other_user = User.objects.create_user(
            phone_number='09120000003', password='X12345678',
            username='other', is_phone_verified=True,
        )
        code = DiscountCode.objects.create(
            code='ONCEONLY', type='fixed', value=10000,
            start_at=now - timedelta(hours=1), end_at=now + timedelta(days=1),
            is_used=True, used_by=other_user, used_at=now,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/auth/discount-codes/apply/', {'code': 'ONCEONLY'})
        self.assertEqual(response.status_code, 400)

    def test_apply_expired_code_rejected(self):
        now = timezone.now()
        DiscountCode.objects.create(
            code='EXPIRED', type='fixed', value=10000,
            start_at=now - timedelta(days=10), end_at=now - timedelta(days=1),
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/auth/discount-codes/apply/', {'code': 'EXPIRED'})
        self.assertEqual(response.status_code, 400)

    def test_apply_future_code_rejected(self):
        now = timezone.now()
        DiscountCode.objects.create(
            code='TOOSOON', type='fixed', value=10000,
            start_at=now + timedelta(days=1), end_at=now + timedelta(days=10),
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/auth/discount-codes/apply/', {'code': 'TOOSOON'})
        self.assertEqual(response.status_code, 400)

    def test_apply_nonexistent_code_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/auth/discount-codes/apply/', {'code': 'DOESNOTEXIST'})
        self.assertEqual(response.status_code, 404)

