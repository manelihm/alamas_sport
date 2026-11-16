from django.core.management.base import BaseCommand
from faker import Faker

from app_auth.models import User
from app_product.models import (
    Category, Product, ProductColor, ProductSize,
    ProductMaterial, ProductOption
)
from app_home.models import HomeContent

fake = Faker()


class Command(BaseCommand):
    help = 'Creates fake sample data for users and products'

    def handle(self, *args, **options):
        self.create_users()
        colors = self.create_colors()
        sizes = self.create_sizes()
        materials = self.create_materials()
        categories = self.create_categories()
        self.create_products(categories, colors, sizes, materials)

        self.stdout.write(self.style.SUCCESS('All fake data created successfully!'))

    def create_users(self):
        self.stdout.write('Creating users...')

        # One super admin (only if none exists yet)
        if not User.objects.filter(role='super_admin').exists():
            User.objects.create_superuser(
                phone_number='09100000001',
                password='SuperAdmin123',
                username='superadmin',
                first_name='Super',
                last_name='Admin',
            )

        # A few regular admins
        for i in range(2):
            phone = f'0910000001{i}'
            if not User.objects.filter(phone_number=phone).exists():
                user = User.objects.create_user(
                    phone_number=phone,
                    password='Admin12345',
                    username=f'admin{i}',
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    role='admin',
                    is_staff=True,
                    is_phone_verified=True,
                )

        # Regular users
        used_phones = set(User.objects.values_list('phone_number', flat=True))
        created = 0
        attempts = 0
        while created < 20 and attempts < 100:
            attempts += 1
            phone = '09' + fake.numerify('#########')
            if phone in used_phones:
                continue
            used_phones.add(phone)
            User.objects.create_user(
                phone_number=phone,
                password='User12345',
                username=fake.unique.user_name(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                gender=fake.random_element(['male', 'female']),
                role='user',
                is_phone_verified=True,
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f'  -> {User.objects.count()} total users now in database.'))

    def create_colors(self):
        self.stdout.write('Creating colors...')
        colors = []
        for _ in range(6):
            color = ProductColor.objects.create(
                name=fake.color_name(),
                color_code=fake.hex_color()
            )
            colors.append(color)
        return colors

    def create_sizes(self):
        self.stdout.write('Creating sizes...')
        sizes = []
        for size_name in ['S', 'M', 'L', 'XL', 'XXL']:
            size, _ = ProductSize.objects.get_or_create(name=size_name)
            sizes.append(size)
        return sizes

    def create_materials(self):
        self.stdout.write('Creating materials...')
        materials = []
        for _ in range(4):
            material = ProductMaterial.objects.create(
                name=fake.word().capitalize(),
                description=fake.sentence(),
              
            )
            materials.append(material)
        return materials

    def create_categories(self):
        self.stdout.write('Creating categories...')
        all_categories = []

        root_categories = []
        for _ in range(4):
            category = Category.objects.create(
                parent=None,
                name=fake.word().capitalize(),
                description=fake.sentence(),
                is_active=True
            )
            root_categories.append(category)
            all_categories.append(category)

        for parent in root_categories:
            for _ in range(3):
                sub = Category.objects.create(
                    parent=parent,
                    name=fake.word().capitalize(),
                    description=fake.sentence(),
                    is_active=True
                )
                all_categories.append(sub)

        return all_categories

    def create_products(self, categories, colors, sizes, materials):
        self.stdout.write('Updating products for Trending...')

        trending_section = HomeContent.objects.filter(
        type='trending'
        ).order_by('id').first()

        if not trending_section:
            trending_section = HomeContent.objects.create(
                type='trending',
                title='Trending Products',
                sort_order=1,
                is_active=True,
            )

    # آخرین ۱۵ محصولی که Seed ساخته است
        products = list(
         Product.objects.order_by('-id')[:15]
        )

        if len(products) < 15:
            self.stdout.write(
                self.style.ERROR(
                    'There are fewer than 15 products in the database.'
                )
            )
            return

    # مرتب‌سازی از قدیمی به جدید
        products.reverse()

        for index, product in enumerate(products):
            is_trending = index < 8

            product.is_trending = is_trending
            product.trending_sort_order = index + 1 if is_trending else 0
            product.trending_is_active = is_trending
            product.trending_home_content = (
                trending_section if is_trending else None
            )

            product.save(update_fields=[
                'is_trending',
                'trending_sort_order',
                'trending_is_active',
                'trending_home_content',
            ])

        self.stdout.write(
            self.style.SUCCESS(
                '15 products updated; 8 products marked as Trending.'
            )
        )